"""
Notion 客户端模块 - 将思考记录写入 Notion 数据库
数据库 Properties:
  - 标题（title）：问题
  - 信息源（multi_select）：关联的新闻来源
  - 问题（rich_text）：当日思考题
  - 回答（rich_text）：用户回复整理后的观点
  - 关键词（multi_select）：AI 提取的关键词
  - 日期（date）：记录日期
  - 原文链接（rich_text）：相关文章链接
"""
import os
import requests
from datetime import datetime, timezone, timedelta
from typing import Optional

NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


def get_token() -> str:
    token = os.environ.get("NOTION_TOKEN", "")
    if not token:
        raise ValueError("NOTION_TOKEN 环境变量未设置")
    return token


def get_database_id() -> str:
    db_id = os.environ.get("NOTION_DATABASE_ID", "")
    if not db_id:
        raise ValueError("NOTION_DATABASE_ID 环境变量未设置")
    return db_id


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {get_token()}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def create_thought_record(
    question: str,
    answer: str,
    sources: list[str],
    keywords: list[str],
    source_links: list[str],
    date_str: Optional[str] = None,
) -> dict:
    """
    在 Notion 数据库中创建一条思考记录

    Args:
        question: 当日思考题
        answer: 整理后的用户观点
        sources: 信息来源名称列表（如 ["TechCrunch AI", "HuggingFace Blog"]）
        keywords: 关键词列表
        source_links: 相关文章链接列表
        date_str: 日期字符串（YYYY-MM-DD），默认今天北京时间
    """
    if not date_str:
        date_str = str((datetime.now(timezone.utc) + timedelta(hours=8)).date())

    # 标题取问题的前 50 字
    title_text = question[:50] + ("…" if len(question) > 50 else "")

    # 原文链接拼接为文本
    links_text = "\n".join(source_links) if source_links else ""

    properties = {
        "标题": {
            "title": [{"text": {"content": title_text}}]
        },
        "问题": {
            "rich_text": [{"text": {"content": question}}]
        },
        "回答": {
            "rich_text": [{"text": {"content": answer[:2000]}}]
        },
        "信息源": {
            "multi_select": [{"name": s[:100]} for s in sources[:10]]
        },
        "关键词": {
            "multi_select": [{"name": k[:100]} for k in keywords[:10]]
        },
        "日期": {
            "date": {"start": date_str}
        },
        "原文链接": {
            "rich_text": [{"text": {"content": links_text[:2000]}}]
        },
    }

    payload = {
        "parent": {"database_id": get_database_id()},
        "properties": properties,
    }

    resp = requests.post(
        f"{NOTION_API}/pages",
        headers=_headers(),
        json=payload,
        timeout=15,
    )

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Notion 写入失败 ({resp.status_code}): {resp.text[:300]}")

    return resp.json()


def ensure_database_properties(database_id: Optional[str] = None) -> dict:
    """
    检查 Notion 数据库是否有所需字段，若无则自动创建
    """
    db_id = database_id or get_database_id()
    resp = requests.get(
        f"{NOTION_API}/databases/{db_id}",
        headers=_headers(),
        timeout=10,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"获取数据库信息失败: {resp.text[:200]}")

    db = resp.json()
    existing = set(db.get("properties", {}).keys())
    required = {"标题", "问题", "回答", "信息源", "关键词", "日期", "原文链接"}
    missing = required - existing

    if missing:
        print(f"[Notion] 数据库缺少字段: {missing}，请参考 docs/notion-setup.md 手动创建")

    return db


if __name__ == "__main__":
    # 测试写入
    result = create_thought_record(
        question="Claude 4 发布对 AI Agent 开发有什么影响？",
        answer="Claude 4 在长上下文和工具调用方面的提升，意味着 Agent 可以处理更复杂的多步任务，减少中间出错率。",
        sources=["Anthropic Blog", "TechCrunch AI"],
        keywords=["Claude 4", "AI Agent", "工具调用", "长上下文"],
        source_links=["https://www.anthropic.com/news/claude-4"],
    )
    print("写入成功，页面 ID:", result.get("id"))
