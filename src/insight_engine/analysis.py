"""
Stage 2: Analysis — 单次 DeepSeek 调用产出 InsightPackage

职责：
- 主题聚类（2-5 theme）
- 叙述合成（每个 theme 的 narrative 是解读而非摘要）
- 信号提取（key_signal 是一句话判断）
- 矛盾检测（tension）
- 跨主题关联（cross_theme_connection）

温度 0.5，max_tokens 2000。
"""

import json
import os
from openai import OpenAI
from prompts import get


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def _get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def _build_articles_text(articles: list[dict]) -> str:
    """将 article list 格式化为 LLM 可读的文本（更精简，突出分析价值）。"""
    lines = []
    for i, a in enumerate(articles, 1):
        title = a.get("title", "")
        source = a.get("source", "")
        link = a.get("link", "")
        summary = a.get("ai_summary", "")
        lines.append(
            f"#{i}\n"
            f"标题: {title}\n"
            f"来源: {source}\n"
            f"链接: {link}\n"
            f"摘要: {summary}\n"
        )
    return "\n".join(lines)


def _strip_fence(raw: str) -> str:
    """移除 DeepSeek 可能包裹的 ```json fence。"""
    content = raw.strip()
    if "```" in content:
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
        content = content.strip()
    return content


def _build_article_list_for_cache(articles: list[dict]) -> list[dict]:
    """构建用于分析的 article 列表（确保标准化）。"""
    return [
        {
            "title": a.get("title", ""),
            "link": a.get("link", ""),
            "source": a.get("source", ""),
            "ai_summary": a.get("ai_summary", ""),
        }
        for a in articles
    ]


def analyze(
    articles: list[dict],
    date: str,
    language: str = "zh",
) -> dict:
    """执行分析，返回 InsightPackage dict。

    Args:
        articles: 经过 ingestion 清洗后的 article list
        date: 日期字符串（YYYY-MM-DD）
        language: "zh" 或 "en"

    Returns:
        符合 InsightPackage 结构的 dict。失败时返回退化的包。
    """
    if not articles:
        print("[Insight] Analysis: 输入为空，返回退化包")
        return {
            "date": date,
            "language": language,
            "article_count": 0,
            "themes": [],
            "key_signal": "",
            "cross_theme_connection": "",
        }

    articles_text = _build_articles_text(articles)

    system_prompt = get("insight_analysis_system", language)
    user_prompt = get("insight_analysis_user", language).format(
        date=date,
        articles_text=articles_text,
        article_count=len(articles),
    )

    client = _get_client()

    print(f"[Insight] Analysis: 发送 {len(articles)} 条文章到 DeepSeek...")
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.5,
        max_tokens=2000,
    )

    raw = response.choices[0].message.content.strip()
    raw = _strip_fence(raw)

    try:
        package = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[Insight] Analysis: JSON 解析失败: {e}")
        print(f"[Insight] Analysis: 原始响应前 200 字符: {raw[:200]}")
        return _build_degraded_package(articles, date, language)

    # 确保缺失字段有默认值
    package.setdefault("date", date)
    package.setdefault("language", language)
    package.setdefault("article_count", len(articles))
    package.setdefault("themes", [])
    package.setdefault("key_signal", "")
    package.setdefault("cross_theme_connection", "")

    print(f"[Insight] Analysis: 完成 — {len(package['themes'])} 个主题, "
          f"key_signal: {package['key_signal'][:60]}...")
    return package


def _build_degraded_package(
    articles: list[dict],
    date: str,
    language: str,
) -> dict:
    """当 LLM 调用失败时的退化包。将所有文章归入一个「未分类」主题。"""
    print("[Insight] Analysis: 使用退化包（所有文章归入一个主题）")
    return {
        "date": date,
        "language": language,
        "article_count": len(articles),
        "themes": [
            {
                "name": "今日 AI 动态" if language == "zh" else "Today's AI Highlights",
                "articles": _build_article_list_for_cache(articles),
                "narrative": "今日 AI 新闻涵盖多个方向，详见原文摘要。",
                "tension": None,
            }
        ],
        "key_signal": "无法生成分析（API 调用异常）。",
        "cross_theme_connection": "",
    }