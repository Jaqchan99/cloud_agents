"""
AI 处理模块 - 使用 DeepSeek API 对新闻进行摘要、筛选和格式化
"""
import os
import json
from openai import OpenAI


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def select_and_summarize(articles: list[dict], config: dict) -> list[dict]:
    """
    让 DeepSeek 从原始文章列表中筛选最有价值的条目并生成中文摘要

    Args:
        articles: 原始文章列表
        config: 用户配置，包含 max_items, focus_topics, user_note 等

    Returns:
        处理后的文章列表，每条包含 ai_summary 字段
    """
    if not articles:
        return []

    max_items = config.get("max_items", 8)
    focus_topics = config.get("focus_topics", [])
    user_note = config.get("user_note", "")

    focus_str = "、".join(focus_topics) if focus_topics else "大语言模型、AI Agent、开源模型、行业动态"
    user_note_str = f"\n用户特别备注：{user_note}" if user_note else ""

    # 构造文章列表供 AI 阅读（截断避免超出 token 限制）
    articles_text = ""
    for i, a in enumerate(articles[:60]):
        articles_text += (
            f"{i+1}. [{a['source']}][{a['category']}] {a['title']}\n"
            f"   摘要: {a['summary'][:200]}\n"
            f"   链接: {a['link']}\n\n"
        )

    system_prompt = (
        "你是一名专注于 AI 领域的资讯编辑，帮助用户筛选和总结最有价值的 AI 资讯。"
        "请用中文回复。"
    )

    user_prompt = f"""以下是今天抓取的 AI 相关文章列表，请完成：

1. 从中选出最值得关注的 {max_items} 条（优先关注：{focus_str}）{user_note_str}
2. 为每条文章生成 2-3 句话的中文简介，说明其核心内容和意义
3. 按重要性从高到低排序

请严格以如下 JSON 数组格式返回，不要包含其他文字：
[
  {{
    "index": <原始编号>,
    "title": "<原始标题>",
    "source": "<来源>",
    "category": "<分类>",
    "link": "<链接>",
    "ai_summary": "<你写的中文摘要>"
  }},
  ...
]

文章列表：
{articles_text}"""

    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=3000,
    )

    raw = response.choices[0].message.content.strip()

    # 提取 JSON（DeepSeek 可能包裹在 ```json ... ``` 中）
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    selected = json.loads(raw)

    # 将原始文章的 link 字段补充回去（防止 AI 截断链接）
    index_map = {i + 1: a for i, a in enumerate(articles[:60])}
    for item in selected:
        original = index_map.get(item.get("index", -1))
        if original and not item.get("link"):
            item["link"] = original["link"]

    return selected


def process_user_command(user_message: str, current_config: dict) -> dict:
    """
    解析用户通过 Telegram 发送的自然语言指令，返回更新后的配置

    Args:
        user_message: 用户发送的消息
        current_config: 当前配置

    Returns:
        dict，包含 reply（回复文本）和 updated_config（可能为 None 表示不更新）
    """
    system_prompt = (
        "你是一名 AI 资讯推送助手，负责管理用户的资讯推送偏好。"
        "请用中文回复，语气友好简洁。"
    )

    config_json = json.dumps(current_config, ensure_ascii=False, indent=2)

    user_prompt = f"""当前用户配置如下：
{config_json}

用户发送了以下消息："{user_message}"

请判断用户意图，并返回如下 JSON 格式（不要包含其他文字）：
{{
  "reply": "<给用户的回复，说明你做了什么调整>",
  "updated_config": <更新后的完整配置 JSON，若无需修改则返回 null>
}}

可调整的配置字段说明：
- focus_topics: list[str]，关注的主题列表
- include_keywords: list[str]，必须包含的关键词
- exclude_keywords: list[str]，过滤掉的关键词  
- max_items: int，每次推送条数（1-15）
- hours_back: int，抓取多少小时内的文章（6-48）
- push_time: str，推送时间，格式 "HH:MM"（UTC）
- user_note: str，给 AI 编辑的特别备注

用户消息示例及对应操作：
- "我只想看 Claude 和 GPT 的新闻" → 更新 include_keywords
- "去掉论文类内容" → 更新 exclude_keywords 或 enabled_sources
- "每次推送 10 条" → 更新 max_items
- "改为早上 8 点推送" → 更新 push_time（注意转换为 UTC）
- "帮我关注 AI 安全方向" → 更新 focus_topics"""

    client = get_client()
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=1500,
    )

    raw = response.choices[0].message.content.strip()

    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    return result


def format_daily_digest(articles: list[dict], date_str: str) -> str:
    """将处理后的文章列表格式化为 Telegram 消息（Markdown 格式）"""
    if not articles:
        return f"📭 *{date_str} AI 日报*\n\n今日暂无符合条件的 AI 资讯。"

    lines = [f"🤖 *{date_str} AI 日报* — 精选 {len(articles)} 条\n"]

    category_icons = {
        "论文": "📄",
        "技术博客": "📝",
        "行业动态": "🏢",
        "行业新闻": "📰",
        "社区讨论": "💬",
    }

    for i, article in enumerate(articles, 1):
        icon = category_icons.get(article.get("category", ""), "🔗")
        title = article.get("title", "无标题")
        link = article.get("link", "")
        summary = article.get("ai_summary", article.get("summary", ""))
        source = article.get("source", "")

        # Telegram MarkdownV2 需要转义特殊字符，这里使用 Markdown（V1）
        lines.append(
            f"{i}\\. {icon} [{_escape_md(title)}]({link})\n"
            f"   _{_escape_md(source)}_\n"
            f"   {_escape_md(summary)}\n"
        )

    lines.append("\n_由 AI News Bot 自动推送 · 发送 /help 查看可用指令_")
    return "\n".join(lines)


def _escape_md(text: str) -> str:
    """转义 Telegram MarkdownV2 特殊字符"""
    special_chars = r"\_*[]()~`>#+-=|{}.!"
    for ch in special_chars:
        text = text.replace(ch, f"\\{ch}")
    return text


if __name__ == "__main__":
    sample_articles = [
        {
            "title": "GPT-5 Released with New Capabilities",
            "link": "https://example.com",
            "summary": "OpenAI releases GPT-5 with improved reasoning and multimodal abilities.",
            "source": "OpenAI Blog",
            "category": "行业动态",
        }
    ]
    sample_config = {"max_items": 5, "focus_topics": ["大语言模型"], "user_note": ""}
    result = select_and_summarize(sample_articles, sample_config)
    print(json.dumps(result, ensure_ascii=False, indent=2))
