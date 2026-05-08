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


def _save_to_notion(
    question: str,
    text: str,
    related_articles: list,
    all_articles: list,
    date_str: str,
) -> tuple[str, list, list, str]:
    """
    公共的 Notion 写入逻辑。
    返回 (notion_url, keywords, final_sources, refined_answer)
    """
    from thought_generator import should_refine, refine_user_reply, extract_keywords_and_sources

    needs_refine = should_refine(text)
    print(f"[Thought] 需要润色: {needs_refine}")

    refined_answer = None
    if needs_refine:
        refined = refine_user_reply(question, text, related_articles)
        refined_answer = refined.get("refined_answer", "")
        keywords = refined.get("keywords", [])
        sources_mentioned = refined.get("sources_mentioned", [])
    else:
        extracted = extract_keywords_and_sources(question, text, related_articles)
        keywords = extracted.get("keywords", [])
        sources_mentioned = extracted.get("sources_mentioned", [])

    # 解析信息来源
    final_sources, final_links = [], []
    for a in related_articles:
        src, link = a.get("source", ""), a.get("link", "")
        if src and src not in final_sources:
            final_sources.append(src)
        if link and link not in final_links:
            final_links.append(link)
    for mention in sources_mentioned:
        mention_lower = mention.lower()
        for a in all_articles:
            if (mention_lower in a.get("title", "").lower()
                    or mention_lower in a.get("source", "").lower()
                    or a.get("source", "").lower() in mention_lower):
                src, link = a.get("source", ""), a.get("link", "")
                if src and src not in final_sources:
                    final_sources.append(src)
                if link and link not in final_links:
                    final_links.append(link)

    notion_url = ""
    notion_enabled = bool(os.environ.get("NOTION_TOKEN")) and bool(os.environ.get("NOTION_DATABASE_ID"))
    if notion_enabled:
        from notion_client import create_thought_record
        result = create_thought_record(
            question=question,
            answer=text,
            sources=final_sources,
            keywords=keywords,
            source_links=final_links,
            date_str=date_str or None,
            refined_answer=refined_answer,
        )
        notion_url = result.get("url", "")
        print(f"[Notion] 写入成功: {notion_url}")
    else:
        print("[Notion] 未配置，跳过写入")

    return notion_url, keywords, final_sources, refined_answer


def _build_notion_reply(
    notion_url: str,
    keywords: list,
    final_sources: list,
    refined_answer: str | None,
    notion_enabled: bool,
) -> str:
    lines = ["✅ **记录已存入 Notion！**\n"]
    if refined_answer:
        lines.append(f"**整理后观点：**\n{refined_answer}\n")
    lines += [
        f"**关键词：** {' · '.join(keywords) if keywords else '—'}",
        f"**信息来源：** {' | '.join(final_sources) if final_sources else '未指定'}",
    ]
    if notion_url:
        lines.append(f"\n📝 [在 Notion 中查看]({notion_url})")
    if not notion_enabled:
        lines.append("\n⚠️ _Notion 未配置，记录未存储。_")
    return "\n".join(lines)


def handle_capture(text: str) -> str | None:
    """
    对长度 > 20 字的非命令消息做意图分类，路由到：
      - "config"  → 返回 None（交由 process_user_command 处理）
      - "answer"  → 今日思考题的回复，以今日问题存入 Notion
      - "note"    → 独立想法，由 AI 生成问题后存入 Notion

    不再使用 answered 标志锁死：每条消息通过消息 ID 去重，均可独立存档。
    """
    from thought_generator import classify_message_intent, generate_question_from_thought, _CONFIG_KEYWORDS

    # config 关键词检查优先于长度过滤：
    # 短命令如"把城市设置为北京"应直接落到 process_user_command，而非被跳过
    if any(kw in text for kw in _CONFIG_KEYWORDS):
        return None  # 交由 process_user_command 处理

    # 对长度 < 20 字的非 config 消息不做 capture（排除短感叹、单字等噪音）
    if len(text) < 20:
        return None

    ctx = load_thought_context()
    today_question = ctx.get("question", "") if ctx else ""
    related_articles = ctx.get("related_articles", []) if ctx else []
    all_articles = ctx.get("all_articles", []) if ctx else []
    date_str = ctx.get("date", "") if ctx else ""

    intent = classify_message_intent(text, today_question)
    print(f"[Intent] 消息意图: {intent}")

    if intent == "config":
        return None  # 交由 process_user_command

    try:
        notion_enabled = bool(os.environ.get("NOTION_TOKEN")) and bool(os.environ.get("NOTION_DATABASE_ID"))

        if intent == "answer":
            # 回答今日思考题：question = 今日思考题
            print(f"[Thought] 识别为思考题回答")
            notion_url, keywords, sources, refined = _save_to_notion(
                question=today_question,
                text=text,
                related_articles=related_articles,
                all_articles=all_articles,
                date_str=date_str,
            )
        else:
            # note：独立想法，AI 生成问题
            print(f"[Thought] 识别为独立想法，生成问题...")
            generated_q = generate_question_from_thought(text)
            print(f"[Thought] 生成问题: {generated_q}")
            notion_url, keywords, sources, refined = _save_to_notion(
                question=generated_q,
                text=text,
                related_articles=[],   # 独立想法不关联今日文章
                all_articles=all_articles,
                date_str=date_str,
            )

        return _build_notion_reply(notion_url, keywords, sources, refined, notion_enabled)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Thought] 处理失败: {e}")
        return f"❌ 处理时出错：{e}\n你的原始回复已收到，请稍后重试。"


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
        if THOUGHT_CONTEXT_PATH.exists():
            with open(THOUGHT_CONTEXT_PATH, "r", encoding="utf-8") as f:
                ctx = json.load(f)
            from thought_generator import format_thought_question_message
            return format_thought_question_message(ctx), None
        return "📭 今日暂无思考题，等待日报推送后自动生成。", None

    # 忽略 Bot 自身发的消息
    if text.startswith("🤖") or text.startswith("📭") or text.startswith("📋") or text.startswith("_由 AI") or text.startswith("---"):
        return "", None

    # 统一意图路由：capture（answer/note） 或 config
    capture_reply = handle_capture(text)
    if capture_reply is not None:
        return capture_reply, None

    # 意图为 config：调用 DeepSeek 修改 user_config
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
