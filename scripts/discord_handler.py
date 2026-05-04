"""
Discord 命令处理脚本 - 由 GitHub Actions 每 15 分钟触发
轮询频道消息，处理用户命令，配置变更自动 commit 持久化
同时作为每日推送守卫：检测当天是否已推送，若漏推则全天任意时刻补发
"""
import sys
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))  # 确保 daily_push 可被导入

from ai_processor import process_user_command
from discord_client import get_messages, send_message, get_channel_id, get_user_id

CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_config.json"
LAST_MSG_ID_PATH = Path(__file__).parent.parent / "config" / "last_discord_msg_id.txt"
LAST_PUSH_DATE_PATH = Path(__file__).parent.parent / "config" / "last_push_date.txt"
THOUGHT_CONTEXT_PATH = Path(__file__).parent.parent / "config" / "today_thought_context.json"

# 守卫检测窗口：北京时间 08:00-23:00（UTC 00:00-15:00）
# 扩大窗口，使任意一次 discord_handler 触发都能补发
PUSH_GUARD_START_BJ = 8   # 北京时间 08:00
PUSH_GUARD_END_BJ = 23    # 北京时间 23:00


def get_beijing_date_str() -> str:
    now = datetime.now(timezone.utc) + timedelta(hours=8)
    return str(now.date())


def get_beijing_hour() -> int:
    now = datetime.now(timezone.utc) + timedelta(hours=8)
    return now.hour


def check_and_trigger_daily_push():
    """
    守卫检测：北京时间 08:00-23:00 内若今天还没推送，直接补发
    主推送由外部 cron-job.org 触发，此处作为最后一道保险
    """
    bj_hour = get_beijing_hour()

    if not (PUSH_GUARD_START_BJ <= bj_hour < PUSH_GUARD_END_BJ):
        print(f"[Guard] 当前北京时间 {bj_hour}:xx，不在守卫窗口（08-23），跳过")
        return

    today = get_beijing_date_str()
    already_pushed = False
    if LAST_PUSH_DATE_PATH.exists():
        last = LAST_PUSH_DATE_PATH.read_text().strip()
        already_pushed = (last == today)

    if already_pushed:
        print(f"[Guard] 今天（{today}）已推送 ✅")
        return

    print(f"[Guard] ⚠️  今天（{today}）尚未推送！北京时间 {bj_hour}:xx，开始补发...")
    try:
        from daily_push import run_daily_push
        run_daily_push(force=False)
        print("[Guard] ✅ 补发成功")
    except Exception as e:
        import traceback
        print(f"[Guard] ❌ 补发失败: {e}")
        traceback.print_exc()
        try:
            send_message(f"⚠️ **AI News Bot**：今日早报补发失败，请手动触发 GitHub Actions。\n错误：`{e}`")
        except Exception:
            pass

HELP_TEXT = """🤖 **AI News Bot 使用指南**

**内置命令：**
`!help` - 查看帮助
`!config` - 查看当前配置
`!status` - 检查运行状态和最后推送时间
`!push` - 立即推送今日 AI 早报

**自然语言调整（直接发消息即可）：**
• 我只想看大模型相关的新闻
• 去掉论文类内容，只要行业新闻
• 每次推送改为 10 条
• 帮我关注 AI 安全和 AI Agent 方向
• 过滤掉关于图像生成的内容
• 天气改成北京

> ⚠️ 使用 GitHub Actions 简化版，命令响应可能有延迟（`!push` 除外，实时执行）。"""


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"[Config] 配置已保存")


def load_last_msg_id() -> str | None:
    if LAST_MSG_ID_PATH.exists():
        val = LAST_MSG_ID_PATH.read_text().strip()
        return val if val else None
    return None


def save_last_msg_id(msg_id: str):
    LAST_MSG_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_MSG_ID_PATH.write_text(msg_id)


def load_thought_context() -> dict | None:
    """加载今日思考题上下文"""
    if THOUGHT_CONTEXT_PATH.exists():
        with open(THOUGHT_CONTEXT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def mark_thought_answered():
    """标记今日思考题已回答"""
    ctx = load_thought_context()
    if ctx:
        ctx["answered"] = True
        with open(THOUGHT_CONTEXT_PATH, "w", encoding="utf-8") as f:
            json.dump(ctx, f, ensure_ascii=False, indent=2)


def try_handle_thought_reply(text: str) -> str | None:
    """
    检测消息是否是对今日思考题的回复。
    如果是，调用 DeepSeek 整理观点并写入 Notion，返回回复文本。
    如果不是，返回 None（交由后续逻辑处理）。

    判断规则：今日思考题存在且未回答，且消息长度 > 20 字（排除短命令）
    """
    ctx = load_thought_context()
    if not ctx:
        return None
    if ctx.get("answered"):
        return None
    if len(text) < 20:
        return None
    # 排除明显的配置调整指令
    config_keywords = ["每次推送", "关注", "过滤", "去掉", "只想看", "改为", "修改", "天气改", "max_items"]
    if any(kw in text for kw in config_keywords):
        return None

    question = ctx.get("question", "")
    related_articles = ctx.get("related_articles", [])
    all_articles = ctx.get("all_articles", [])
    date_str = ctx.get("date", "")

    try:
        # 用 DeepSeek 整理观点
        from thought_generator import refine_user_reply
        print(f"[Thought] 检测到思考题回复，开始整理观点...")
        refined = refine_user_reply(question, text, related_articles)

        refined_answer = refined.get("refined_answer", text)
        keywords = refined.get("keywords", [])
        sources_mentioned = refined.get("sources_mentioned", [])

        # 解析用户提到的信息源（匹配到 all_articles 中的具体来源）
        final_sources = []
        final_links = []

        # 先加入思考题关联的文章来源
        for a in related_articles:
            src = a.get("source", "")
            if src and src not in final_sources:
                final_sources.append(src)
            link = a.get("link", "")
            if link and link not in final_links:
                final_links.append(link)

        # 再根据用户提到的内容匹配额外来源
        for mention in sources_mentioned:
            mention_lower = mention.lower()
            for a in all_articles:
                title_lower = a.get("title", "").lower()
                source_lower = a.get("source", "").lower()
                if (mention_lower in title_lower or mention_lower in source_lower
                        or source_lower in mention_lower):
                    src = a.get("source", "")
                    link = a.get("link", "")
                    if src and src not in final_sources:
                        final_sources.append(src)
                    if link and link not in final_links:
                        final_links.append(link)

        # 写入 Notion
        notion_enabled = bool(os.environ.get("NOTION_TOKEN")) and bool(os.environ.get("NOTION_DATABASE_ID"))
        notion_url = ""

        if notion_enabled:
            from notion_client import create_thought_record
            result = create_thought_record(
                question=question,
                answer=refined_answer,
                sources=final_sources,
                keywords=keywords,
                source_links=final_links,
                date_str=date_str if date_str else None,
            )
            notion_url = result.get("url", "")
            print(f"[Notion] 记录写入成功: {notion_url}")
        else:
            print("[Notion] 未配置 NOTION_TOKEN，跳过写入")

        mark_thought_answered()

        # 构建回复
        reply_lines = [
            "✅ **观点已整理并存入 Notion！**\n",
            f"**整理后的观点：**\n{refined_answer}\n",
            f"**关键词：** {' · '.join(keywords)}\n",
            f"**信息来源：** {' | '.join(final_sources) if final_sources else '未指定'}",
        ]
        if notion_url:
            reply_lines.append(f"\n📝 [在 Notion 中查看]({notion_url})")
        if not notion_enabled:
            reply_lines.append("\n⚠️ _Notion 未配置，观点仅整理未存储。配置 NOTION_TOKEN 后可自动存档。_")

        return "\n".join(reply_lines)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Thought] 处理回复失败: {e}")
        return f"❌ 整理观点时出错：{e}\n你的原始回复已收到，请稍后重试。"


def handle_command(text: str, config: dict) -> tuple[str, dict | None]:
    """处理命令，返回 (回复文本, 更新后的配置或None)"""
    text = text.strip()

    if text in ("!start", "!help"):
        return HELP_TEXT, None

    if text == "!config":
        config_str = json.dumps(config, ensure_ascii=False, indent=2)
        return f"⚙️ **当前配置：**\n```json\n{config_str}\n```", None

    if text == "!status":
        last_push = "未知"
        if LAST_PUSH_DATE_PATH.exists():
            last_push = LAST_PUSH_DATE_PATH.read_text().strip()
        return f"✅ AI News Bot 运行正常！\n📅 最后推送日期：{last_push}\n⏰ 每天北京时间 09:00 自动推送。", None

    if text == "!push":
        try:
            from daily_push import run_daily_push
            run_daily_push(force=True)
            return "✅ 已立即推送今日 AI 早报！", None
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"❌ 推送失败：{e}", None

    if text == "!thought":
        # 重新发送今日思考题
        if THOUGHT_CONTEXT_PATH.exists():
            with open(THOUGHT_CONTEXT_PATH, "r", encoding="utf-8") as f:
                ctx = json.load(f)
            if ctx.get("answered"):
                return "✅ 今日思考题你已回答过，记录已存入 Notion。", None
            from thought_generator import format_thought_question_message
            return format_thought_question_message(ctx), None
        return "📭 今日暂无思考题，等待日报推送后自动生成。", None

    # 忽略 Bot 自身发的消息
    if text.startswith("🤖") or text.startswith("📭") or text.startswith("📋") or text.startswith("_由 AI") or text.startswith("---"):
        return "", None

    # 检测是否是对今日思考题的回复
    thought_reply = try_handle_thought_reply(text)
    if thought_reply is not None:
        return thought_reply, None

    # 自然语言处理配置调整
    try:
        result = process_user_command(text, config)
        reply = result.get("reply", "已处理您的请求。")
        updated_config = result.get("updated_config")
        return reply, updated_config
    except Exception as e:
        print(f"[Handler] AI 处理失败: {e}")
        return f"❌ 处理失败：{e}\n请重试或检查 API 配置。", None


def run_handler():
    """轮询并处理新消息，同时执行每日推送守卫检测"""
    print("[Handler] 开始处理 Discord 消息...")

    # 每日推送守卫：优先检测是否需要补发
    check_and_trigger_daily_push()

    my_user_id = get_user_id()
    last_msg_id = load_last_msg_id()
    config = load_config()

    messages = get_messages(after_id=last_msg_id, limit=20)

    if not messages:
        print("[Handler] 无新消息")
        return

    print(f"[Handler] 收到 {len(messages)} 条新消息")
    config_changed = False
    latest_msg_id = last_msg_id

    for msg in messages:
        msg_id = msg.get("id", "")
        author = msg.get("author", {})
        author_id = str(author.get("id", ""))
        is_bot = author.get("bot", False)
        content = msg.get("content", "").strip()

        # 更新最新消息 ID
        if msg_id:
            latest_msg_id = msg_id

        # 忽略 Bot 自身的消息
        if is_bot:
            continue

        # 安全过滤：只响应指定用户
        if my_user_id and author_id != str(my_user_id):
            print(f"[Handler] 忽略来自未知用户的消息: user_id={author_id}")
            continue

        if not content:
            continue

        print(f"[Handler] 处理消息: {content[:80]}")

        reply, updated_config = handle_command(content, config)

        if not reply:
            continue

        if updated_config:
            config = updated_config
            config_changed = True

        try:
            # 长回复自动分割
            if len(reply) > 1900:
                from discord_client import send_long_message
                send_long_message(reply)
            else:
                send_message(reply)
        except Exception as e:
            print(f"[Handler] 发送回复失败: {e}")

    if latest_msg_id and latest_msg_id != last_msg_id:
        save_last_msg_id(latest_msg_id)

    if config_changed:
        save_config(config)
        print("[Handler] 配置已更新并保存")

    print("[Handler] 处理完成")


if __name__ == "__main__":
    run_handler()
