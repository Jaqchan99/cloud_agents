"""
Telegram 命令处理脚本 - 由 GitHub Actions 定时触发，轮询处理用户消息

由于是 GitHub Actions 简化版（无长期运行的 webhook），
此脚本每隔一段时间（例如每 15 分钟）运行一次，处理期间收到的所有消息。
处理后的 update_id 保存到 config/last_update_id.txt 避免重复处理。
"""
import sys
import json
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ai_processor import process_user_command
from telegram_client import get_updates, send_html_message, get_chat_id, send_long_message

CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_config.json"
LAST_UPDATE_ID_PATH = Path(__file__).parent.parent / "config" / "last_update_id.txt"

HELP_TEXT = """🤖 <b>AI News Bot 使用指南</b>

<b>内置命令：</b>
/help - 查看帮助
/config - 查看当前配置
/status - 检查 Bot 状态

<b>自然语言调整（直接发送消息即可）：</b>
• 「我只想看大模型相关的新闻」
• 「去掉论文类内容，只要行业新闻」
• 「每次推送改为 10 条」
• 「帮我关注 AI 安全和 AI Agent 方向」
• 「过滤掉关于图像生成的内容」

<b>注意：</b> 由于使用 GitHub Actions 简化版，
消息响应可能有 5-15 分钟延迟。"""


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"[Config] 配置已保存: {CONFIG_PATH}")


def load_last_update_id() -> int:
    if LAST_UPDATE_ID_PATH.exists():
        try:
            return int(LAST_UPDATE_ID_PATH.read_text().strip())
        except ValueError:
            pass
    return 0


def save_last_update_id(update_id: int):
    LAST_UPDATE_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_UPDATE_ID_PATH.write_text(str(update_id))


def handle_command(text: str, config: dict) -> tuple[str, dict | None]:
    """处理命令，返回 (回复文本, 更新后的配置或None)"""
    text = text.strip()

    if text in ("/start", "/help"):
        return HELP_TEXT, None

    if text == "/config":
        config_str = json.dumps(config, ensure_ascii=False, indent=2)
        return f"⚙️ <b>当前配置：</b>\n<pre>{config_str}</pre>", None

    if text == "/status":
        return "✅ AI News Bot 运行正常！下次推送时间请查看 GitHub Actions 配置。", None

    # 自然语言处理
    try:
        result = process_user_command(text, config)
        reply = result.get("reply", "已处理您的请求。")
        updated_config = result.get("updated_config")
        return reply, updated_config
    except Exception as e:
        print(f"[Handler] AI 处理失败: {e}")
        return f"❌ 处理失败：{e}\n请重试或检查 API 配置。", None


def run_handler():
    """轮询并处理新消息"""
    print("[Handler] 开始处理 Telegram 消息...")

    my_chat_id = get_chat_id()
    last_update_id = load_last_update_id()
    config = load_config()

    offset = last_update_id + 1 if last_update_id > 0 else None
    updates = get_updates(offset=offset, timeout=5)

    if not updates:
        print("[Handler] 无新消息")
        return

    print(f"[Handler] 收到 {len(updates)} 条更新")
    config_changed = False

    for update in updates:
        update_id = update.get("update_id", 0)
        message = update.get("message") or update.get("edited_message")

        if not message:
            save_last_update_id(update_id)
            continue

        # 只响应来自指定 chat_id 的消息（安全过滤）
        chat_id = str(message.get("chat", {}).get("id", ""))
        if chat_id != str(my_chat_id):
            print(f"[Handler] 忽略来自未知用户的消息: chat_id={chat_id}")
            save_last_update_id(update_id)
            continue

        text = message.get("text", "").strip()
        if not text:
            save_last_update_id(update_id)
            continue

        print(f"[Handler] 处理消息: {text[:80]}")

        reply, updated_config = handle_command(text, config)

        if updated_config:
            config = updated_config
            config_changed = True

        try:
            send_long_message(reply, chat_id=chat_id)
        except Exception as e:
            print(f"[Handler] 发送回复失败: {e}")

        save_last_update_id(update_id)

    if config_changed:
        save_config(config)
        print("[Handler] 配置已更新并保存")

    print("[Handler] 处理完成")


if __name__ == "__main__":
    run_handler()
