"""
每日推送主脚本 - 由 GitHub Actions 定时触发
支持 Discord 和 Telegram 两种推送端，通过环境变量 PUSH_CHANNEL 切换（默认 discord）
推送完成后生成每日思考题，等待用户回复后写入 Notion
"""
import sys
import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_fetcher import fetch_all_news
from ai_processor import select_and_summarize
from weather_fetcher import get_weather, weather_to_text
from morning_greeter import generate_morning_greeting
from prompts import get

CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_config.json"
LAST_PUSH_DATE_PATH = Path(__file__).parent.parent / "config" / "last_push_date.txt"
THOUGHT_CONTEXT_PATH = Path(__file__).parent.parent / "config" / "today_thought_context.json"

# Test channel paths
TEST_CONFIG_PATH = Path(__file__).parent.parent / "config" / "test_config.json"
TEST_LAST_PUSH_DATE_PATH = Path(__file__).parent.parent / "config" / "last_push_date_test.txt"


def _resolve_channel(channel: str) -> dict:
    """Return channel-specific settings."""
    if channel == "test":
        return {
            "config_path": TEST_CONFIG_PATH,
            "last_push_date_path": TEST_LAST_PUSH_DATE_PATH,
            "thought_context_path": None,  # No thought context for test
            "channel_id_env": "DISCORD_TEST_CHANNEL_ID",
        }
    return {
        "config_path": CONFIG_PATH,
        "last_push_date_path": LAST_PUSH_DATE_PATH,
        "thought_context_path": THOUGHT_CONTEXT_PATH,
        "channel_id_env": "DISCORD_CHANNEL_ID",
    }


def get_push_channel() -> str:
    return os.environ.get("PUSH_CHANNEL", "discord").lower()


def get_today_str(lang: str = "zh") -> str:
    """返回北京时间今日日期字符串"""
    from datetime import timedelta
    now_utc = datetime.now(timezone.utc)
    beijing = now_utc + timedelta(hours=8)
    if lang == "en":
        return beijing.strftime("%B %d, %Y")
    return f"{beijing.year}年{beijing.month}月{beijing.day}日"


def has_pushed_today(push_date_path: Path) -> bool:
    if push_date_path.exists():
        last = push_date_path.read_text().strip()
        today = (datetime.now(timezone.utc) + timedelta(hours=8)).date()
        if last == str(today):
            print(f"[Guard] 今天（{today}）已推送过，跳过")
            return True
    return False


def mark_pushed_today(push_date_path: Path):
    today = (datetime.now(timezone.utc) + timedelta(hours=8)).date()
    push_date_path.parent.mkdir(parents=True, exist_ok=True)
    push_date_path.write_text(str(today))
    print(f"[Guard] 已写入推送记录: {push_date_path} = {today}")


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


def save_thought_context(question_data: dict, selected: list[dict], date_str: str):
    """保存思考题上下文到本地"""
    from datetime import timedelta
    iso_date = str((datetime.now(timezone.utc) + timedelta(hours=8)).date())
    context = {
        "date": iso_date,
        "question": question_data.get("question", ""),
        "context": question_data.get("context", ""),
        "related_articles": question_data.get("related_articles", []),
        "all_articles": [
            {"title": a.get("title", ""), "source": a.get("source", ""),
             "link": a.get("link", ""), "ai_summary": a.get("ai_summary", "")}
            for a in selected
        ],
        "answered": False,
    }
    THOUGHT_CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(THOUGHT_CONTEXT_PATH, "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)
    print(f"[Thought] 思考题上下文已保存")


def send_via_discord(greeting: str, articles: list[dict], date_str: str,
                     fallback_text: str = "", channel_id: str = None, lang: str = "zh"):
    from discord_client import send_digest, send_message, send_long_message
    if not articles:
        send_message(fallback_text, channel_id=channel_id)
        return
    if greeting:
        send_message(greeting, channel_id=channel_id)
    send_digest(articles, date_str, channel_id=channel_id, lang=lang)


def send_via_telegram(greeting: str, articles: list[dict], date_str: str,
                      fallback_text: str = ""):
    from telegram_client import send_long_message, format_html_digest
    if not articles:
        send_long_message(fallback_text)
        return
    if greeting:
        send_long_message(greeting)
    message = format_html_digest(articles, date_str)
    send_long_message(message)


def run_daily_push(force: bool = False, channel: str = "main"):
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] 开始每日推送 (channel={channel})...")

    ch = _resolve_channel(channel)
    config_path = ch["config_path"]
    push_date_path = ch["last_push_date_path"]
    thought_path = ch["thought_context_path"]
    channel_id_env = ch["channel_id_env"]

    if not force and has_pushed_today(push_date_path):
        return

    channel_type = get_push_channel()
    print(f"[Config] 推送端: {channel_type}")

    config = load_config(config_path)
    lang = config.get("language", "zh")
    print(f"[Config] 语言: {lang}")
    print(f"[Config] 关注主题: {config.get('focus_topics')}")
    print(f"[Config] 最大推送数: {config.get('max_items')}")

    date_str = get_today_str(lang)
    weather_location = config.get("weather_location", "Shanghai")
    target_channel_id = os.environ.get(channel_id_env, "")

    # 1. 获取天气
    print(f"[Step 1] 获取 {weather_location} 天气...")
    weather = get_weather(weather_location)
    weather_text = weather_to_text(weather, lang=lang)
    print(f"[Step 1] {weather_text}")

    # 2. 抓取新闻
    print("[Step 2] 抓取新闻...")
    articles = fetch_all_news(config)

    if not articles:
        print("[Warning] 未抓取到任何文章")
        fallback = get("digest_empty", lang).format(date_str=date_str)
        if channel_type == "telegram":
            send_via_telegram("", [], date_str, fallback)
        else:
            send_via_discord("", [], date_str, fallback, channel_id=target_channel_id, lang=lang)
        return

    # 3. AI 筛选与总结
    print(f"[Step 3] 使用 DeepSeek 处理 {len(articles)} 条文章...")
    selected = select_and_summarize(articles, config)

    if not selected:
        print("[Warning] AI 筛选结果为空")
        fallback = get("digest_empty", lang).format(date_str=date_str)
        if channel_type == "telegram":
            send_via_telegram("", [], date_str, fallback)
        else:
            send_via_discord("", [], date_str, fallback, channel_id=target_channel_id, lang=lang)
        return

    print(f"[Step 3] AI 筛选出 {len(selected)} 条")

    # 4. 生成问候语
    print("[Step 4] 生成早报问候语...")
    greeting = generate_morning_greeting(weather_text, len(selected), date_str, lang=lang)
    print(f"[Step 4] 问候语: {greeting[:80]}...")

    # 5. 发送日报
    print(f"[Step 5] 通过 {channel_type} 发送...")
    if channel_type == "telegram":
        send_via_telegram(greeting, selected, date_str)
    else:
        send_via_discord(greeting, selected, date_str, channel_id=target_channel_id, lang=lang)

    # 6. 生成并发送思考题（test 频道跳过）
    if thought_path is not None:
        print("[Step 6] 生成每日思考题...")
        try:
            from thought_generator import generate_thought_question, format_thought_question_message
            question_data = generate_thought_question(selected, date_str, lang=lang)
            thought_msg = format_thought_question_message(question_data, lang=lang)

            if channel_type == "telegram":
                from telegram_client import send_long_message
                send_long_message(thought_msg)
            else:
                from discord_client import send_message
                send_message(thought_msg, channel_id=target_channel_id)

            save_thought_context(question_data, selected, date_str)
            print(f"[Step 6] 思考题已发送: {question_data.get('question','')[:60]}...")
        except Exception as e:
            print(f"[Step 6] 思考题生成失败（不影响日报推送）: {e}")
    else:
        print("[Step 6] 测试频道，跳过思考题生成")

    # 记录今日已推送
    mark_pushed_today(push_date_path)
    print("[Done] 推送完成！")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="强制推送，忽略今日已推送检测")
    parser.add_argument("--channel", choices=["main", "test"], default="main",
                        help="推送频道（main=生产, test=测试）")
    args = parser.parse_args()
    run_daily_push(force=args.force, channel=args.channel)
