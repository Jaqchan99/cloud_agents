"""
Discord 命令处理脚本 - 由 GitHub Actions 每 15 分钟触发
轮询频道消息，处理用户命令，配置变更自动 commit 持久化
同时作为每日推送守卫：检测当天是否已推送，若漏推则全天任意时刻补发

支持双频道：主频道（生产）和测试频道（隔离配置）
"""
import sys
import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

from ai_processor import process_user_command
from discord_client import get_messages, send_message, get_channel_id, get_user_id
from prompts import get

# ── 生产频道路径 ──
CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_config.json"
LAST_MSG_ID_PATH = Path(__file__).parent.parent / "config" / "last_discord_msg_id.txt"
LAST_PUSH_DATE_PATH = Path(__file__).parent.parent / "config" / "last_push_date.txt"
THOUGHT_CONTEXT_PATH = Path(__file__).parent.parent / "config" / "today_thought_context.json"

# ── 测试频道路径 ──
TEST_CONFIG_PATH = Path(__file__).parent.parent / "config" / "test_config.json"
TEST_LAST_MSG_ID_PATH = Path(__file__).parent.parent / "config" / "last_discord_msg_id_test.txt"
TEST_LAST_PUSH_DATE_PATH = Path(__file__).parent.parent / "config" / "last_push_date_test.txt"
TEST_THOUGHT_CONTEXT_PATH = Path(__file__).parent.parent / "config" / "today_thought_context_test.json"

PUSH_GUARD_START_BJ = 8
PUSH_GUARD_END_BJ = 23


def _resolve_channel(channel: str) -> dict:
    if channel == "test":
        return {
            "config_path": TEST_CONFIG_PATH,
            "last_msg_id_path": TEST_LAST_MSG_ID_PATH,
            "last_push_date_path": TEST_LAST_PUSH_DATE_PATH,
            "thought_context_path": TEST_THOUGHT_CONTEXT_PATH,
            "channel_id_env": "DISCORD_TEST_CHANNEL_ID",
            "skip_guard": True,
        }
    return {
        "config_path": CONFIG_PATH,
        "last_msg_id_path": LAST_MSG_ID_PATH,
        "last_push_date_path": LAST_PUSH_DATE_PATH,
        "thought_context_path": THOUGHT_CONTEXT_PATH,
        "channel_id_env": "DISCORD_CHANNEL_ID",
        "skip_guard": False,
    }


def get_beijing_date_str() -> str:
    now = datetime.now(timezone.utc) + timedelta(hours=8)
    return str(now.date())


def get_beijing_hour() -> int:
    now = datetime.now(timezone.utc) + timedelta(hours=8)
    return now.hour


def check_and_trigger_daily_push():
    """守卫检测：北京时间 08:00-23:00 内若今天还没推送，直接补发"""
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
        run_daily_push(force=False, channel="main")
        print("[Guard] ✅ 补发成功")
    except Exception as e:
        import traceback
        print(f"[Guard] ❌ 补发失败: {e}")
        traceback.print_exc()
        try:
            send_message(f"⚠️ **AI News Bot**：今日早报补发失败，请手动触发 GitHub Actions。\n错误：`{e}`")
        except Exception:
            pass


def load_config(config_path: Path) -> dict:
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return get_default_config()


def get_default_config() -> dict:
    return {
        "push_channel": "discord",
        "language": "zh",
        "focus_topics": ["大语言模型", "AI Agent", "开源模型", "多模态"],
        "include_keywords": [],
        "exclude_keywords": [],
        "max_items": 8,
        "hours_back": 72,
        "push_time": "01:00",
        "include_hacker_news": True,
        "user_note": "",
        "weather_location": "Shanghai",
        "enabled_sources": [
            "TechCrunch AI",
            "VentureBeat AI",
            "The Verge AI",
            "Ars Technica",
            "HuggingFace Blog",
            "OpenAI Blog",
            "Google AI Blog",
            "Arxiv AI",
            "Arxiv ML",
        ],
    }


def save_config(config: dict, config_path: Path):
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print(f"[Config] 配置已保存: {config_path}")


def load_last_msg_id(msg_id_path: Path) -> str | None:
    if msg_id_path.exists():
        val = msg_id_path.read_text().strip()
        return val if val else None
    return None


def save_last_msg_id(msg_id: str, msg_id_path: Path):
    msg_id_path.parent.mkdir(parents=True, exist_ok=True)
    msg_id_path.write_text(msg_id)


def load_thought_context() -> dict | None:
    if THOUGHT_CONTEXT_PATH.exists():
        with open(THOUGHT_CONTEXT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def _save_to_notion(
    question: str,
    text: str,
    related_articles: list,
    all_articles: list,
    date_str: str,
    lang: str = "zh",
) -> tuple[str, list, list, str]:
    from thought_generator import should_refine, refine_user_reply, extract_keywords_and_sources

    needs_refine = should_refine(text, lang=lang)
    print(f"[Thought] 需要润色: {needs_refine}")

    refined_answer = None
    if needs_refine:
        refined = refine_user_reply(question, text, related_articles, lang=lang)
        refined_answer = refined.get("refined_answer", "")
        keywords = refined.get("keywords", [])
        sources_mentioned = refined.get("sources_mentioned", [])
    else:
        extracted = extract_keywords_and_sources(question, text, related_articles, lang=lang)
        keywords = extracted.get("keywords", [])
        sources_mentioned = extracted.get("sources_mentioned", [])

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
    lang: str = "zh",
) -> str:
    if lang == "en":
        lines = ["✅ **Saved to Notion!**\n"]
        if refined_answer:
            lines.append(f"**Organized view:**\n{refined_answer}\n")
        lines += [
            f"**Keywords:** {' · '.join(keywords) if keywords else '—'}",
            f"**Sources:** {' | '.join(final_sources) if final_sources else 'unspecified'}",
        ]
        if notion_url:
            lines.append(f"\n📝 [View in Notion]({notion_url})")
        if not notion_enabled:
            lines.append("\n⚠️ _Notion not configured, record not stored._")
    else:
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


def handle_capture(text: str, lang: str = "zh") -> str | None:
    """对长度 > 20 字的非命令消息做意图分类，路由到 answer/note"""
    from thought_generator import classify_message_intent, generate_question_from_thought
    from prompts import CONFIG_KEYWORDS

    # config 关键词检查优先
    if any(kw in text.lower() for kw in CONFIG_KEYWORDS):
        return None

    if len(text) < 20:
        return None

    ctx = load_thought_context()
    today_question = ctx.get("question", "") if ctx else ""
    related_articles = ctx.get("related_articles", []) if ctx else []
    all_articles = ctx.get("all_articles", []) if ctx else []
    date_str = ctx.get("date", "") if ctx else ""

    intent = classify_message_intent(text, today_question, lang=lang)
    print(f"[Intent] 消息意图: {intent}")

    if intent == "config":
        return None

    try:
        notion_enabled = bool(os.environ.get("NOTION_TOKEN")) and bool(os.environ.get("NOTION_DATABASE_ID"))

        if intent == "answer":
            print(f"[Thought] 识别为思考题回答")
            notion_url, keywords, sources, refined = _save_to_notion(
                question=today_question,
                text=text,
                related_articles=related_articles,
                all_articles=all_articles,
                date_str=date_str,
                lang=lang,
            )
        else:
            print(f"[Thought] 识别为独立想法，生成问题...")
            generated_q = generate_question_from_thought(text, lang=lang)
            print(f"[Thought] 生成问题: {generated_q}")
            notion_url, keywords, sources, refined = _save_to_notion(
                question=generated_q,
                text=text,
                related_articles=[],
                all_articles=all_articles,
                date_str=date_str,
                lang=lang,
            )

        return _build_notion_reply(notion_url, keywords, sources, refined, notion_enabled, lang=lang)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Thought] 处理失败: {e}")
        return f"❌ Error: {e}\nYour reply has been received, please retry later." if lang == "en" \
               else f"❌ 处理时出错：{e}\n你的原始回复已收到，请稍后重试。"


def handle_command(text: str, config: dict, channel: str = "main",
                   channel_id: str = "", last_push_date_path: Path = LAST_PUSH_DATE_PATH) -> tuple[str, dict | None]:
    """处理命令，返回 (回复文本, 更新后的配置或None)"""
    text = text.strip()
    lang = config.get("language", "zh")

    if text in ("!start", "!help"):
        return get("help_text", lang), None

    if text == "!config":
        config_str = json.dumps(config, ensure_ascii=False, indent=2)
        prefix = "⚙️ **Current Config:**" if lang == "en" else "⚙️ **当前配置：**"
        return f"{prefix}\n```json\n{config_str}\n```", None

    if text == "!status":
        last_push = "Unknown" if lang == "en" else "未知"
        if last_push_date_path.exists():
            last_push = last_push_date_path.read_text().strip()
        return get("status_template", lang).format(last_push=last_push), None

    if text == "!push":
        try:
            from daily_push import run_daily_push
            run_daily_push(force=True, channel=channel)
            ok = "✅ Test push completed! Check the test channel." if lang == "en" else \
                 "✅ 已立即推送今日 AI 早报！"
            return ok, None
        except Exception as e:
            import traceback
            traceback.print_exc()
            err = f"❌ Push failed: {e}" if lang == "en" else f"❌ 推送失败：{e}"
            return err, None

    if text == "!thought":
        if THOUGHT_CONTEXT_PATH.exists():
            with open(THOUGHT_CONTEXT_PATH, "r", encoding="utf-8") as f:
                ctx = json.load(f)
            from thought_generator import format_thought_question_message
            return format_thought_question_message(ctx, lang=lang), None
        empty = "📭 No thought question yet. Wait for the daily digest." if lang == "en" else \
               "📭 今日暂无思考题，等待日报推送后自动生成。"
        return empty, None

    # 忽略 Bot 自身发的消息
    if text.startswith("🤖") or text.startswith("📭") or text.startswith("📋") or text.startswith("_由 AI") \
            or text.startswith("---") or text.startswith("_Auto-pushed"):
        return "", None

    # 统一意图路由：capture（answer/note） 或 config
    capture_reply = handle_capture(text, lang=lang)
    if capture_reply is not None:
        return capture_reply, None

    # 意图为 config：调用 DeepSeek 修改配置
    try:
        result = process_user_command(text, config)
        reply = result.get("reply", "Done." if lang == "en" else "已处理您的请求。")
        updated_config = result.get("updated_config")
        return reply, updated_config
    except Exception as e:
        print(f"[Handler] AI 处理失败: {e}")
        err = f"❌ Error: {e}\nPlease retry." if lang == "en" else f"❌ 处理失败：{e}\n请重试或检查 API 配置。"
        return err, None


def run_handler(channel: str = "main"):
    """轮询并处理新消息，同时执行每日推送守卫检测"""
    ch = _resolve_channel(channel)
    config_path = ch["config_path"]
    last_msg_id_path = ch["last_msg_id_path"]
    last_push_date_path = ch["last_push_date_path"]
    channel_id_env = ch["channel_id_env"]
    skip_guard = ch["skip_guard"]

    print(f"[Handler] 开始处理 Discord 消息 (channel={channel})...")

    # 每日推送守卫（仅生产频道）
    if not skip_guard:
        check_and_trigger_daily_push()

    my_user_id = get_user_id()
    last_msg_id = load_last_msg_id(last_msg_id_path)
    config = load_config(config_path)
    lang = config.get("language", "zh")

    # 获取目标频道 ID
    target_channel_id = os.environ.get(channel_id_env, "")
    if not target_channel_id:
        print(f"[Handler] ⚠️ {channel_id_env} 未设置，跳过 {channel} 频道")
        return

    messages = get_messages(channel_id=target_channel_id, after_id=last_msg_id, limit=20)

    if not messages:
        print(f"[Handler] {channel} 频道无新消息")
        return

    print(f"[Handler] {channel} 频道收到 {len(messages)} 条新消息")
    config_changed = False
    latest_msg_id = last_msg_id

    for msg in messages:
        msg_id = msg.get("id", "")
        author = msg.get("author", {})
        author_id = str(author.get("id", ""))
        is_bot = author.get("bot", False)
        content = msg.get("content", "").strip()

        if msg_id:
            latest_msg_id = msg_id

        if is_bot:
            continue

        if my_user_id and author_id != str(my_user_id):
            print(f"[Handler] 忽略来自未知用户的消息: user_id={author_id}")
            continue

        if not content:
            continue

        print(f"[Handler] 处理消息: {content[:80]}")

        # ── 测试频道特殊命令：reset ──
        if channel == "test" and content.strip().lower() in ("测试", "test"):
            config = get_default_config()
            save_config(config, config_path)
            lang = config.get("language", "zh")
            reply = get("test_reset_message", lang)
            try:
                from discord_client import send_long_message
                send_long_message(reply, channel_id=target_channel_id)
            except Exception as e:
                print(f"[Handler] 发送重置消息失败: {e}")
            config_changed = True
            continue

        reply, updated_config = handle_command(
            content, config, channel=channel,
            channel_id=target_channel_id,
            last_push_date_path=last_push_date_path,
        )

        if not reply:
            continue

        if updated_config:
            config = updated_config
            config_changed = True

        try:
            if len(reply) > 1900:
                from discord_client import send_long_message
                send_long_message(reply, channel_id=target_channel_id)
            else:
                send_message(reply, channel_id=target_channel_id)
        except Exception as e:
            print(f"[Handler] 发送回复失败: {e}")

    if latest_msg_id and latest_msg_id != last_msg_id:
        save_last_msg_id(latest_msg_id, last_msg_id_path)

    if config_changed:
        save_config(config, config_path)
        print("[Handler] 配置已更新并保存")

    print(f"[Handler] {channel} 处理完成")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", choices=["main", "test"], default="main",
                        help="目标频道（main=生产, test=测试）")
    args = parser.parse_args()
    run_handler(channel=args.channel)
