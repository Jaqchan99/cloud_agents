"""
Pipeline orchestrator — 串联 ingestion → cache → analysis → renderers。

职责：
- 读取 today_thought_context.json 的 all_articles
- Stage 1 ingestion（验证/去重/标准化，零 LLM）
- 缓存命中检查；未命中则 Stage 2 analysis（1 次 LLM）并写入缓存
- Stage 3 渲染（每格式 1 次 LLM），输出到 output/insight/{date}/{format}.md

公共入口：run_insight_pipeline(formats, language)
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from .ingestion import load_from_thought_context, ingest
from .cache import get_cache, set_cache
from .analysis import analyze
from .renderers import RENDERERS


BEIJING_TZ = timezone(timedelta(hours=8))
DEFAULT_CONTEXT_PATH = Path(__file__).parent.parent.parent / "config" / "today_thought_context.json"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent.parent / "output" / "insight"

DEFAULT_FORMATS = ["linkedin", "newsletter", "podcast_script", "bilingual"]


def _today_date_beijing() -> str:
    """返回北京时间今天的 YYYY-MM-DD。"""
    return datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")


def _load_articles_and_date(context_path: Path) -> tuple[list[dict], str]:
    """从 thought context 读取 all_articles 与 date。

    date 优先取 context 中的字段；缺失则用北京时间今天。
    """
    try:
        with open(context_path, "r", encoding="utf-8") as f:
            ctx = json.load(f)
    except FileNotFoundError:
        print(f"[Insight] Pipeline: context 文件不存在: {context_path}")
        return [], _today_date_beijing()
    except json.JSONDecodeError as e:
        print(f"[Insight] Pipeline: context JSON 解析失败: {e}")
        return [], _today_date_beijing()

    articles = ctx.get("all_articles", [])
    date = ctx.get("date") or _today_date_beijing()
    print(f"[Insight] Pipeline: context date={date}, all_articles={len(articles)}")
    return articles, date


def _get_or_build_package(
    articles: list[dict],
    date: str,
    language: str,
) -> dict:
    """缓存优先：命中则直接返回，未命中则调用 analysis 并写缓存。"""
    links = [a.get("link", "") for a in articles]

    cached = get_cache(date, links, language)
    if cached is not None:
        print(f"[Insight] Pipeline: 使用缓存 InsightPackage（{cached.get('article_count', 0)} 篇）")
        return cached

    print("[Insight] Pipeline: 缓存未命中 → 调用 analysis")
    package = analyze(articles, date=date, language=language)

    try:
        set_cache(date, links, language, package)
    except Exception as e:
        print(f"[Insight] Pipeline: 写缓存失败（不影响流程）— {type(e).__name__}: {e}")

    return package


def _render_one(format_name: str, package: dict) -> tuple[str, str]:
    """调用单个 renderer，返回 (format_name, rendered_text)。"""
    renderer = RENDERERS.get(format_name)
    if renderer is None:
        err_msg = f"[Insight] Pipeline: 未知格式 '{format_name}'，跳过"
        print(err_msg)
        return format_name, err_msg
    try:
        text = renderer(package)
    except Exception as e:
        print(f"[Insight] Pipeline: 渲染 {format_name} 抛出异常 — {type(e).__name__}: {e}")
        return format_name, f"# 渲染失败（{format_name}）\n\n原因：{type(e).__name__}: {e}"
    print(f"[Insight] Pipeline: 渲染 {format_name} → OK（{len(text)} 字符）")
    return format_name, text


def _render_all(formats: list[str], package: dict, parallel: bool = True) -> dict[str, str]:
    """渲染所有请求的格式。parallel=True 时使用线程池并行调用。"""
    results: dict[str, str] = {}
    if not parallel or len(formats) <= 1:
        for fmt in formats:
            results[fmt] = _render_one(fmt, package)[1]
        return results

    with ThreadPoolExecutor(max_workers=min(len(formats), 4)) as ex:
        future_map = {ex.submit(_render_one, fmt, package): fmt for fmt in formats}
        for fut in as_completed(future_map):
            fmt, text = fut.result()
            results[fmt] = text
    return results


def _write_outputs(date: str, rendered: dict[str, str], output_dir: Path) -> dict[str, Path]:
    """将每个格式的渲染结果写入 output/insight/{date}/{format}.md。"""
    day_dir = output_dir / date
    day_dir.mkdir(parents=True, exist_ok=True)

    paths: dict[str, Path] = {}
    for fmt, text in rendered.items():
        path = day_dir / f"{fmt}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        paths[fmt] = path
        print(f"[Insight] Pipeline: 写入 {path}（{len(text)} 字符）")
    return paths


def run_insight_pipeline(
    formats: Optional[list[str]] = None,
    language: str = "zh",
    context_path: Optional[Path | str] = None,
    output_dir: Optional[Path | str] = None,
    parallel: bool = True,
    write_files: bool = True,
) -> dict:
    """执行完整 Insight 流水线。

    Args:
        formats: 要渲染的格式列表，None 则使用 DEFAULT_FORMATS
        language: "zh" 或 "en"
        context_path: today_thought_context.json 路径，None 用默认
        output_dir: 输出目录，None 用默认 output/insight/
        parallel: 是否并行渲染
        write_files: 是否落盘到 output/insight/{date}/

    Returns:
        {
            "date": str,
            "language": str,
            "article_count": int,
            "package": dict,            # InsightPackage
            "rendered": {fmt: text},    # 渲染结果
            "output_paths": {fmt: path} # 落盘路径（write_files=True 时）
        }
    """
    formats = formats or DEFAULT_FORMATS
    ctx_path = Path(context_path) if context_path else DEFAULT_CONTEXT_PATH
    out_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR

    print(f"[Insight] Pipeline: 启动 — formats={formats}, language={language}")
    print(f"[Insight] Pipeline: context={ctx_path}")
    print(f"[Insight] Pipeline: output_dir={out_dir}")

    # Stage 1: ingestion
    raw_articles, date = _load_articles_and_date(ctx_path)
    articles = ingest(raw_articles)

    if not articles:
        print("[Insight] Pipeline: ingestion 后文章为空，提前退出")
        return {
            "date": date,
            "language": language,
            "article_count": 0,
            "package": {},
            "rendered": {},
            "output_paths": {},
        }

    # Stage 2: cache + analysis
    package = _get_or_build_package(articles, date, language)

    # Stage 3: render
    print(f"[Insight] Pipeline: 开始渲染 {len(formats)} 个格式（parallel={parallel}）")
    rendered = _render_all(formats, package, parallel=parallel)

    # 输出落盘
    output_paths = {}
    if write_files:
        output_paths = _write_outputs(date, rendered, out_dir)

    print(f"[Insight] Pipeline: 完成 — date={date}, articles={len(articles)}, "
          f"formats={list(rendered.keys())}")
    return {
        "date": date,
        "language": language,
        "article_count": len(articles),
        "package": package,
        "rendered": rendered,
        "output_paths": output_paths,
    }
