"""
早报问候语生成模块 - 用 DeepSeek 结合天气生成个性化问候和导语
"""
import os
from datetime import datetime, timezone
from openai import OpenAI

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def get_client() -> OpenAI:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY 未设置")
    return OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL)


def generate_morning_greeting(weather_text: str, news_count: int, date_str: str) -> str:
    """
    生成个性化早报开场白，包含：
    - 对 Jocelyn 的问候
    - 天气播报 + 出行/生活注意事项
    - 今日 AI 日报的简短导语

    返回格式化后的文本（Discord markdown）
    """
    now_utc = datetime.now(timezone.utc)
    # 转换为北京时间（UTC+8）
    hour_cn = (now_utc.hour + 8) % 24
    weekday_cn = WEEKDAY_CN[now_utc.weekday()]

    if 5 <= hour_cn < 10:
        time_greeting = "早上好"
    elif 10 <= hour_cn < 13:
        time_greeting = "上午好"
    elif 13 <= hour_cn < 18:
        time_greeting = "下午好"
    elif 18 <= hour_cn < 22:
        time_greeting = "晚上好"
    else:
        time_greeting = "夜深了，注意休息"

    prompt = f"""今天是 {date_str}（{weekday_cn}），当前北京时间约 {hour_cn} 点。
天气数据：{weather_text}
今日 AI 日报共收录 {news_count} 条精选资讯。

请你作为一个贴心的 AI 助手，为用户 Jocelyn 生成一段温暖的早报开场白，要求：

1. **问候语**（1-2句）：用"{time_greeting}，Jocelyn！"开头，结合日期/星期和天气，语气自然亲切
2. **天气 + 出行/生活提示**（2-3句）：根据天气数据给出实用的今日注意事项，如是否需要带伞、防晒、多穿衣等，语气贴心不啰嗦
3. **AI 日报导语**（1句）：用简短一句话自然过渡到今日 AI 资讯，点出今天大模型/AI 领域有什么值得关注，带一点好奇心引导

格式要求：
- 使用 Discord markdown（**加粗**、换行用 \\n）
- 总长度控制在 150 字以内
- 不要加任何标题或编号
- 直接输出正文，不要有前缀说明"""

    try:
        client = get_client()
        response = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[
                {"role": "system", "content": "你是一个温暖、简洁、有品味的 AI 助手，擅长写每日早报开场白。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[Greeter] 问候语生成失败: {e}")
        return _fallback_greeting(time_greeting, weather_text, date_str, weekday_cn)


def _fallback_greeting(time_greeting: str, weather_text: str, date_str: str, weekday_cn: str) -> str:
    """API 调用失败时的备用问候语"""
    return (
        f"**{time_greeting}，Jocelyn！** 今天是 {date_str}（{weekday_cn}）。\n"
        f"{weather_text}\n"
        f"以下是今日精选 AI 资讯，一起来看看 AI 世界今天发生了什么 ↓"
    )
