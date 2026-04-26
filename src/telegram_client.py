"""
Telegram 客户端模块 - 负责发送消息到 Telegram
"""
import os
import requests
from typing import Optional


TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def get_bot_token() -> str:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN 环境变量未设置")
    return token


def get_chat_id() -> str:
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not chat_id:
        raise ValueError("TELEGRAM_CHAT_ID 环境变量未设置")
    return chat_id


def send_message(
    text: str,
    chat_id: Optional[str] = None,
    parse_mode: str = "MarkdownV2",
    disable_web_page_preview: bool = True,
) -> dict:
    """发送消息到 Telegram"""
    token = get_bot_token()
    target_chat_id = chat_id or get_chat_id()

    url = TELEGRAM_API.format(token=token, method="sendMessage")
    payload = {
        "chat_id": target_chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
    }

    resp = requests.post(url, json=payload, timeout=15)
    result = resp.json()

    if not result.get("ok"):
        # 如果 MarkdownV2 解析失败，退回纯文本重试
        if parse_mode != "HTML":
            print(f"[Telegram] Markdown 发送失败，尝试纯文本: {result.get('description')}")
            return send_message(text, chat_id=chat_id, parse_mode="HTML")
        raise RuntimeError(f"Telegram 发送失败: {result.get('description')}")

    return result


def send_long_message(text: str, chat_id: Optional[str] = None) -> list[dict]:
    """
    发送长消息（Telegram 单条消息限制 4096 字符，自动分割）
    """
    results = []
    max_len = 4000

    if len(text) <= max_len:
        results.append(send_message(text, chat_id=chat_id))
        return results

    # 按换行符切分，尽量保持消息完整性
    chunks = []
    current_chunk = ""
    for line in text.split("\n"):
        if len(current_chunk) + len(line) + 1 > max_len:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk = current_chunk + "\n" + line if current_chunk else line

    if current_chunk:
        chunks.append(current_chunk)

    for chunk in chunks:
        results.append(send_message(chunk, chat_id=chat_id))

    return results


def get_updates(offset: Optional[int] = None, timeout: int = 10) -> list[dict]:
    """
    获取 Bot 收到的消息更新（用于 GitHub Actions 轮询处理命令）

    Args:
        offset: 上次处理的 update_id + 1，避免重复处理
        timeout: 长轮询超时时间（秒）
    """
    token = get_bot_token()
    url = TELEGRAM_API.format(token=token, method="getUpdates")
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset

    resp = requests.get(url, params=params, timeout=timeout + 5)
    result = resp.json()

    if not result.get("ok"):
        print(f"[Telegram] getUpdates 失败: {result.get('description')}")
        return []

    return result.get("result", [])


def send_html_message(text: str, chat_id: Optional[str] = None) -> dict:
    """发送 HTML 格式消息"""
    return send_message(text, chat_id=chat_id, parse_mode="HTML")


def format_html_digest(articles: list[dict], date_str: str) -> str:
    """将文章列表格式化为 HTML 消息（比 MarkdownV2 更稳定）"""
    if not articles:
        return f"📭 <b>{date_str} AI 日报</b>\n\n今日暂无符合条件的 AI 资讯。"

    lines = [f"🤖 <b>{date_str} AI 日报</b> — 精选 {len(articles)} 条\n"]

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

        lines.append(
            f'{i}. {icon} <a href="{link}">{_escape_html(title)}</a>\n'
            f'   <i>{_escape_html(source)}</i>\n'
            f'   {_escape_html(summary)}\n'
        )

    lines.append("\n<i>由 AI News Bot 自动推送 · 发送 /help 查看可用指令</i>")
    return "\n".join(lines)


def _escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if token and chat_id:
        result = send_html_message("✅ AI News Bot 测试消息发送成功！", chat_id=chat_id)
        print(result)
    else:
        print("请设置 TELEGRAM_BOT_TOKEN 和 TELEGRAM_CHAT_ID 环境变量")
