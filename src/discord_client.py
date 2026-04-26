"""
Discord 客户端模块 - 负责发送消息到 Discord 频道，以及轮询读取用户消息
使用 Discord REST API（无需长连接 Gateway）
"""
import os
import requests
from typing import Optional

DISCORD_API = "https://discord.com/api/v10"


def get_bot_token() -> str:
    token = os.environ.get("DISCORD_BOT_TOKEN", "")
    if not token:
        raise ValueError("DISCORD_BOT_TOKEN 环境变量未设置")
    return token


def get_channel_id() -> str:
    channel_id = os.environ.get("DISCORD_CHANNEL_ID", "")
    if not channel_id:
        raise ValueError("DISCORD_CHANNEL_ID 环境变量未设置")
    return channel_id


def get_user_id() -> str:
    return os.environ.get("DISCORD_USER_ID", "")


def _headers() -> dict:
    return {"Authorization": f"Bot {get_bot_token()}", "Content-Type": "application/json"}


def send_message(content: str, channel_id: Optional[str] = None) -> dict:
    """发送普通文本消息到 Discord 频道"""
    target = channel_id or get_channel_id()
    url = f"{DISCORD_API}/channels/{target}/messages"

    # Discord 单条消息限制 2000 字符
    if len(content) > 2000:
        return send_long_message(content, channel_id=channel_id)[-1]

    payload = {"content": content}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=15)
    result = resp.json()

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Discord 发送失败 ({resp.status_code}): {result.get('message')}")
    return result


def send_long_message(content: str, channel_id: Optional[str] = None) -> list[dict]:
    """自动分割超长消息"""
    results = []
    max_len = 1900
    target = channel_id or get_channel_id()
    url = f"{DISCORD_API}/channels/{target}/messages"

    chunks = []
    current = ""
    for line in content.split("\n"):
        if len(current) + len(line) + 1 > max_len:
            if current:
                chunks.append(current)
            current = line
        else:
            current = current + "\n" + line if current else line
    if current:
        chunks.append(current)

    for chunk in chunks:
        payload = {"content": chunk}
        resp = requests.post(url, headers=_headers(), json=payload, timeout=15)
        if resp.status_code in (200, 201):
            results.append(resp.json())
        else:
            print(f"[Discord] 分块发送失败: {resp.status_code} {resp.text}")
    return results


def send_embed(title: str, description: str, fields: list[dict] | None = None,
               color: int = 0x5865F2, channel_id: Optional[str] = None) -> dict:
    """发送 Embed 格式消息（更美观）"""
    target = channel_id or get_channel_id()
    url = f"{DISCORD_API}/channels/{target}/messages"

    embed = {
        "title": title[:256],
        "description": description[:4096],
        "color": color,
    }
    if fields:
        embed["fields"] = fields[:25]

    payload = {"embeds": [embed]}
    resp = requests.post(url, headers=_headers(), json=payload, timeout=15)
    result = resp.json()

    if resp.status_code not in (200, 201):
        raise RuntimeError(f"Discord Embed 发送失败 ({resp.status_code}): {result.get('message')}")
    return result


def get_messages(channel_id: Optional[str] = None, after_id: Optional[str] = None,
                 limit: int = 20) -> list[dict]:
    """
    获取频道消息（用于轮询处理用户命令）
    after_id: 只获取该消息 ID 之后的消息，避免重复处理
    """
    target = channel_id or get_channel_id()
    url = f"{DISCORD_API}/channels/{target}/messages"
    params = {"limit": limit}
    if after_id:
        params["after"] = after_id

    resp = requests.get(url, headers=_headers(), params=params, timeout=10)
    if resp.status_code != 200:
        print(f"[Discord] 获取消息失败: {resp.status_code} {resp.text}")
        return []

    messages = resp.json()
    # Discord 返回最新在前，倒序使其按时间正序
    return list(reversed(messages))


def format_digest_embeds(articles: list[dict], date_str: str) -> tuple[str, list[dict]]:
    """
    将文章列表格式化为 Discord Embed 格式
    返回 (header_text, embeds_list)，分批发送
    """
    if not articles:
        return f"📭 **{date_str} AI 日报**\n\n今日暂无符合条件的 AI 资讯。", []

    header = f"🤖 **{date_str} AI 日报** — 精选 {len(articles)} 条\n"

    category_icons = {
        "论文": "📄",
        "技术博客": "📝",
        "行业动态": "🏢",
        "行业新闻": "📰",
        "社区讨论": "💬",
    }

    embeds = []
    for article in articles:
        icon = category_icons.get(article.get("category", ""), "🔗")
        title = article.get("title", "无标题")[:256]
        link = article.get("link", "")
        summary = article.get("ai_summary", article.get("summary", ""))[:1024]
        source = article.get("source", "")
        category = article.get("category", "")

        embed = {
            "title": f"{icon} {title}",
            "url": link,
            "description": summary,
            "color": 0x5865F2,
            "footer": {"text": f"{source} · {category}"},
        }
        embeds.append(embed)

    return header, embeds


def send_digest(articles: list[dict], date_str: str, channel_id: Optional[str] = None):
    """发送每日日报，使用 Embed 卡片格式"""
    target = channel_id or get_channel_id()
    url = f"{DISCORD_API}/channels/{target}/messages"

    header, embeds = format_digest_embeds(articles, date_str)

    # 先发标题
    send_message(header, channel_id=target)

    # Discord 每次最多发 10 个 Embed，分批发送
    batch_size = 10
    for i in range(0, len(embeds), batch_size):
        batch = embeds[i:i + batch_size]
        payload = {"embeds": batch}
        resp = requests.post(url, headers=_headers(), json=payload, timeout=15)
        if resp.status_code not in (200, 201):
            print(f"[Discord] Embed 批次 {i} 发送失败: {resp.status_code} {resp.text}")

    # 发送页脚
    send_message(
        "_由 AI News Bot 自动推送 · 发送 `!help` 查看可用指令_",
        channel_id=target,
    )
