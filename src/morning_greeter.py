"""
早报问候语生成模块 - 用 DeepSeek 结合天气生成个性化问候和导语
"""
import os
from datetime import datetime, timezone
from openai import OpenAI
from prompts import get, get_time_greeting, get_weekday_name

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def generate_morning_greeting(weather_text: str, news_count: int, date_str: str, lang: str = "zh") -> str:
    """
    生成个性化早报开场白，包含：
    - 对 Jocelyn 的问候
    - 天气播报 + 出行/生活注意事项
    - 今日 AI 日报的简短导语

    返回格式化后的文本（Discord markdown）
    """
    now_utc = datetime.now(timezone.utc)
    hour_cn = (now_utc.hour + 8) % 24
    weekday = get_weekday_name(lang, now_utc.weekday())
    time_greeting = get_time_greeting(lang, hour_cn)

    prompt = get("greeting_user", lang).format(
        date_str=date_str,
        weekday=weekday,
        hour=hour_cn,
        weather_text=weather_text,
        news_count=news_count,
        time_greeting=time_greeting,
    )

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": get("greeting_system", lang)},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Greeter] 问候语生成失败: {e}")
        return _fallback_greeting(time_greeting, weather_text, date_str, weekday, lang)


def _fallback_greeting(time_greeting: str, weather_text: str, date_str: str, weekday: str, lang: str = "zh") -> str:
    """API 调用失败时的备用问候语"""
    return get("greeting_fallback", lang).format(
        time_greeting=time_greeting,
        date_str=date_str,
        weekday=weekday,
        weather_text=weather_text,
    )
