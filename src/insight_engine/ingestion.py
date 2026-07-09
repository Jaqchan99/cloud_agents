"""
Stage 1: Ingestion — 验证、去重、标准化

从 today_thought_context.json 的 all_articles 字段读取原始文章数据，
产出验证通过的标准化 article list，供分析阶段使用。

零 LLM 调用。纯数据处理。
"""

from typing import Any


def load_from_thought_context(filepath: str) -> list[dict]:
    """从 today_thought_context.json 读取 all_articles 字段。

    Args:
        filepath: today_thought_context.json 的路径

    Returns:
        all_articles 列表（原始 dict）。关键路径失败时返回空列表。
    """
    import json
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            ctx = json.load(f)
        articles = ctx.get("all_articles", [])
        if not articles:
            print(f"[Insight] Ingestion: all_articles 为空")
            return []
        print(f"[Insight] Ingestion: 从 {filepath} 读取 {len(articles)} 条文章")
        return articles
    except FileNotFoundError:
        print(f"[Insight] Ingestion: 文件不存在: {filepath}")
        return []
    except json.JSONDecodeError as e:
        print(f"[Insight] Ingestion: JSON 解析失败: {e}")
        return []


REQUIRED_FIELDS = {"title", "link", "ai_summary"}


def _validate_article(a: dict) -> bool:
    """检查单条 article 是否包含必填字段且非空。"""
    for field in REQUIRED_FIELDS:
        val = a.get(field)
        if not val or not isinstance(val, str) or not val.strip():
            return False
    return True


def _dedup_by_link(articles: list[dict]) -> list[dict]:
    """按 link 去重，保留首次出现的条目。"""
    seen: set[str] = set()
    result = []
    for a in articles:
        link = a.get("link", "").strip()
        if not link or link in seen:
            continue
        seen.add(link)
        result.append(a)
    return result


def _normalize_article(a: dict) -> dict:
    """标准化文章字段，确保下游格式一致。"""
    return {
        "title": (a.get("title") or "").strip(),
        "link": (a.get("link") or "").strip(),
        "source": (a.get("source") or "").strip(),
        "ai_summary": (a.get("ai_summary") or "").strip(),
    }


def ingest(articles: list[dict]) -> list[dict]:
    """执行 ingestion 流水线：验证 → 去重 → 标准化。

    Args:
        articles: 原始 article list（来自 today_thought_context.json 的 all_articles）

    Returns:
        清洗后的 article list（标准化 dict）。可能为空列表。
    """
    if not articles:
        print("[Insight] Ingestion: 输入为空，跳过")
        return []

    total = len(articles)

    # 验证
    valid = [a for a in articles if _validate_article(a)]
    invalid_count = total - len(valid)
    if invalid_count:
        print(f"[Insight] Ingestion: 移除了 {invalid_count} 条不完整的文章")

    # 去重
    deduped = _dedup_by_link(valid)
    dup_count = len(valid) - len(deduped)
    if dup_count:
        print(f"[Insight] Ingestion: 去重移除了 {dup_count} 条重复文章")

    # 标准化
    normalized = [_normalize_article(a) for a in deduped]

    print(f"[Insight] Ingestion: {total} 条 → {len(normalized)} 条有效文章")
    return normalized