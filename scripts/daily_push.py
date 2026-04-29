"""
每日推送主脚本 - 由 GitHub Actions 定时触发
支持 Discord 和 Telegram 两种推送端，通过环境变量 PUSH_CHANNEL 切换（默认 discord）
"""
import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_fetcher import fetch_all_news
from ai_processor import select_and_summarize
from weather_fetcher import get_weather, weather_to_text
from morning_greeter import generate_morning_greeting

CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_config.json"
LAST_PUSH_DATE_PATH = Path(__file__).parent.parent / "config" / "last_push_date.txt"


def get_push_channel() -> str:
    return os.environ.get("PUSH_CHANNEL", "discord").lower()


def get_today_str() -> str:
    """返回北京时间今日日期字符串，用于去重"""
    now_utc = datetime.now(timezone.utc)
    # UTC+8
    hour_offset = 8
    beijing_hour = (now_utc.hour + hour_offset) % 24
    if now_utc.hour + hour_offset >= 24:
        from datetime import timedelta
        beijing_date = (now_utc + timedelta(hours=hour_offset)).date()
    else:
        beijing_date = now_utc.date()
    return str(beijing_date)


def has_pushed_today() -> bool:
    """检查今天是否已经成功推送过"""
    if LAST_PUSH_DATE_PATH.exists():
        last = LAST_PUSH_DATE_PATH.read_text().strip()
        today = get_today_str()
        if last == today:
            print(f"[Guard] 今天（{today}）已推送过，跳过")
            return True
    return False


def mark_pushed_today():
    """记录今天已推送"""
    today = get_today_str()
    LAST_PUSH_DATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_PUSH_DATE_PATH.write_text(today)
    print(f"[Guard] 已写入推送记录: {LAST_PUSH_DATE_PATH} = {today}")


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return get_default_config()


def get_default_config() -> dict:
    return {
        "push_channel": "discord",
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


def send_via_discord(greeting: str, articles: list[dict], date_str: str, fallback_text: str = ""):
    from discord_client import send_digest, send_message, send_long_message
    if not articles:
        send_message(fallback_text)
        return
    # 先发问候语（独立消息，更醒目）
    if greeting:
        send_message(greeting)
    send_digest(articles, date_str)


def send_via_telegram(greeting: str, articles: list[dict], date_str: str, fallback_text: str = ""):
    from telegram_client import send_long_message, format_html_digest
    if not articles:
        send_long_message(fallback_text)
        return
    if greeting:
        send_long_message(greeting)
    message = format_html_digest(articles, date_str)
    send_long_message(message)


def run_daily_push(force: bool = False):
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] 开始每日推送...")

    if not force and has_pushed_today():
        return

    channel = get_push_channel()
    print(f"[Config] 推送端: {channel}")

    config = load_config()
    print(f"[Config] 关注主题: {config.get('focus_topics')}")
    print(f"[Config] 最大推送数: {config.get('max_items')}")

    date_str = datetime.now(timezone.utc).strftime("%Y年%m月%d日")
    weather_location = config.get("weather_location", "Shanghai")

    # 1. 获取天气
    print(f"[Step 1] 获取 {weather_location} 天气...")
    weather = get_weather(weather_location)
    weather_text = weather_to_text(weather)
    print(f"[Step 1] {weather_text}")

    # 2. 抓取新闻
    print("[Step 2] 抓取新闻...")
    articles = fetch_all_news(config)

    if not articles:
        print("[Warning] 未抓取到任何文章")
        fallback = f"📭 {date_str} AI 日报\n\n今日暂未抓取到 AI 资讯，请稍后重试。"
        if channel == "telegram":
            send_via_telegram("", [], date_str, fallback)
        else:
            send_via_discord("", [], date_str, fallback)
        return

    # 3. AI 筛选与总结
    print(f"[Step 3] 使用 DeepSeek 处理 {len(articles)} 条文章...")
    selected = select_and_summarize(articles, config)

    if not selected:
        print("[Warning] AI 筛选结果为空")
        fallback = f"📭 {date_str} AI 日报\n\n今日 AI 处理未返回结果，请检查 API 配置。"
        if channel == "telegram":
            send_via_telegram("", [], date_str, fallback)
        else:
            send_via_discord("", [], date_str, fallback)
        return

    print(f"[Step 3] AI 筛选出 {len(selected)} 条")

    # 4. 生成问候语
    print("[Step 4] 生成早报问候语...")
    greeting = generate_morning_greeting(weather_text, len(selected), date_str)
    print(f"[Step 4] 问候语: {greeting[:80]}...")

    # 5. 发送
    print(f"[Step 5] 通过 {channel} 发送...")
    if channel == "telegram":
        send_via_telegram(greeting, selected, date_str)
    else:
        send_via_discord(greeting, selected, date_str)

    # 记录今日已推送，防止重复发送
    mark_pushed_today()
    print("[Done] 推送完成！")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="强制推送，忽略今日已推送检测")
    args = parser.parse_args()
    run_daily_push(force=args.force)
