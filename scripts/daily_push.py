"""
每日推送主脚本 - 由 GitHub Actions 定时触发
"""
import sys
import os
import json
from datetime import datetime, timezone
from pathlib import Path

# 将 src 目录加入 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from news_fetcher import fetch_all_news
from ai_processor import select_and_summarize
from telegram_client import send_long_message, format_html_digest

CONFIG_PATH = Path(__file__).parent.parent / "config" / "user_config.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return get_default_config()


def get_default_config() -> dict:
    return {
        "focus_topics": ["大语言模型", "AI Agent", "开源模型", "多模态"],
        "include_keywords": [],
        "exclude_keywords": [],
        "max_items": 8,
        "hours_back": 24,
        "push_time": "01:00",
        "include_hacker_news": True,
        "user_note": "",
        "enabled_sources": [
            "Arxiv AI",
            "Arxiv ML",
            "HuggingFace Blog",
            "OpenAI Blog",
            "Google AI Blog",
            "VentureBeat AI",
            "The Verge AI",
        ],
    }


def run_daily_push():
    print(f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC] 开始每日推送...")

    config = load_config()
    print(f"[Config] 关注主题: {config.get('focus_topics')}")
    print(f"[Config] 最大推送数: {config.get('max_items')}")

    # 1. 抓取新闻
    print("[Step 1] 抓取新闻...")
    articles = fetch_all_news(config)

    if not articles:
        print("[Warning] 未抓取到任何文章，发送提示消息")
        date_str = datetime.now(timezone.utc).strftime("%Y年%m月%d日")
        send_long_message(f"📭 {date_str} AI 日报\n\n今日暂未抓取到 AI 资讯，请稍后重试。")
        return

    # 2. AI 筛选与总结
    print(f"[Step 2] 使用 DeepSeek 处理 {len(articles)} 条文章...")
    selected = select_and_summarize(articles, config)

    if not selected:
        print("[Warning] AI 筛选结果为空")
        date_str = datetime.now(timezone.utc).strftime("%Y年%m月%d日")
        send_long_message(f"📭 {date_str} AI 日报\n\n今日 AI 处理未返回结果，请检查 API 配置。")
        return

    print(f"[Step 2] AI 筛选出 {len(selected)} 条")

    # 3. 格式化并发送
    date_str = datetime.now(timezone.utc).strftime("%Y年%m月%d日")
    message = format_html_digest(selected, date_str)

    print(f"[Step 3] 发送消息（{len(message)} 字符）...")
    send_long_message(message)
    print("[Done] 推送完成！")


if __name__ == "__main__":
    run_daily_push()
