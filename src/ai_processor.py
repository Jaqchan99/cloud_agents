"""
AI 处理模块 - 使用 DeepSeek API 对新闻进行摘要、筛选和格式化
"""
import os
import json
from openai import OpenAI
from prompts import get

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 环境变量未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def select_and_summarize(articles: list[dict], config: dict) -> list[dict]:
    """
    让 DeepSeek 从原始文章列表中筛选最有价值的条目并生成摘要

    Args:
        articles: 原始文章列表
        config: 用户配置，包含 max_items, focus_topics, user_note, language 等

    Returns:
        处理后的文章列表，每条包含 ai_summary 字段
    """
    if not articles:
        return []

    lang = config.get("language", "zh")
    max_items = config.get("max_items", 8)
    focus_topics = config.get("focus_topics", [])
    user_note = config.get("user_note", "")

    focus_fallback = get("select_summarize_focus_fallback", lang)
    focus_str = "、".join(focus_topics) if focus_topics else focus_fallback

    user_note_str = ""
    if user_note:
        user_note_str = get("select_summarize_user_note_prefix", lang).format(user_note=user_note)

    # 构造文章列表供 AI 阅读（截断避免超出 token 限制）
    articles_text = ""
    for i, a in enumerate(articles[:60]):
        articles_text += (
            f"{i+1}. [{a['source']}][{a['category']}] {a['title']}\n"
            f"   summary: {a['summary'][:200]}\n"
            f"   link: {a['link']}\n\n"
        )

    system_prompt = get("select_summarize_system", lang)
    user_prompt = get("select_summarize_user", lang).format(
        max_items=max_items,
        focus_str=focus_str,
        user_note_str=user_note_str,
        articles_text=articles_text,
    )

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
    解析用户通过 Discord 发送的自然语言指令，返回更新后的配置

    Args:
        user_message: 用户发送的消息
        current_config: 当前配置

    Returns:
        dict，包含 reply（回复文本）和 updated_config（可能为 None 表示不更新）
    """
    lang = current_config.get("language", "zh")
    system_prompt = get("process_command_system", lang)

    config_json = json.dumps(current_config, ensure_ascii=False, indent=2)
    user_prompt = get("process_command_user", lang).format(
        config_json=config_json,
        user_message=user_message,
    )

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
