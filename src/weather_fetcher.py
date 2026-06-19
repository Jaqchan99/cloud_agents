"""
天气获取模块 - 使用 wttr.in 免费 API，无需 API Key
"""
import requests
from datetime import datetime, timezone


def get_weather(location: str = "Shanghai") -> dict:
    """
    获取指定城市天气信息
    location: 城市名（英文或中文拼音，如 Shanghai / Beijing / Shenzhen）
    """
    try:
        url = f"https://wttr.in/{location}?format=j1"
        headers = {"User-Agent": "Mozilla/5.0 (compatible; AINewsBot/1.0)"}
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return _fallback(location)

        data = resp.json()
        curr = data["current_condition"][0]
        today = data["weather"][0]
        tomorrow = data["weather"][1] if len(data["weather"]) > 1 else None

        # 当前天气
        temp_c = int(curr["temp_C"])
        feels_like = int(curr["FeelsLikeC"])
        humidity = int(curr["humidity"])
        desc = curr["weatherDesc"][0]["value"]
        wind_speed = int(curr["windspeedKmph"])
        uv_index = int(today.get("uvIndex", curr.get("uvIndex", 0)))

        # 今日最高/最低
        max_temp = int(today["maxtempC"])
        min_temp = int(today["mintempC"])

        # 今日降水概率
        hourly = today.get("hourly", [])
        precip_chance = max([int(h.get("chanceofrain", 0)) for h in hourly], default=0)

        # 明日天气
        tomorrow_desc = ""
        tomorrow_max = ""
        if tomorrow:
            tomorrow_desc = tomorrow["hourly"][4]["weatherDesc"][0]["value"] if tomorrow.get("hourly") else ""
            tomorrow_max = int(tomorrow["maxtempC"])

        return {
            "location": location,
            "temp_c": temp_c,
            "feels_like": feels_like,
            "humidity": humidity,
            "description": desc,
            "wind_speed_kmph": wind_speed,
            "uv_index": uv_index,
            "today_max": max_temp,
            "today_min": min_temp,
            "precip_chance": precip_chance,
            "tomorrow_desc": tomorrow_desc,
            "tomorrow_max": tomorrow_max,
            "success": True,
        }
    except Exception as e:
        print(f"[Weather] 获取天气失败: {e}")
        return _fallback(location)


def _fallback(location: str) -> dict:
    return {
        "location": location,
        "success": False,
        "description": "暂无天气数据",
        "temp_c": None,
        "feels_like": None,
        "humidity": None,
        "wind_speed_kmph": None,
        "uv_index": 0,
        "today_max": None,
        "today_min": None,
        "precip_chance": 0,
        "tomorrow_desc": "",
        "tomorrow_max": "",
    }


def weather_to_text(w: dict, lang: str = "zh") -> str:
    """将天气数据转为给 AI 使用的描述文本"""
    from prompts import get

    if not w.get("success"):
        return get("weather_fallback", lang)

    desc_map = get("weather_desc_map", lang)
    desc = desc_map.get(w["description"], w["description"])
    tomorrow_desc = desc_map.get(w.get("tomorrow_desc", ""), w.get("tomorrow_desc", ""))

    text = get("weather_text_template", lang).format(
        desc=desc,
        temp=w["temp_c"],
        feels_like=w["feels_like"],
        high=w["today_max"],
        low=w["today_min"],
        humidity=w["humidity"],
    )
    # 追加风速/紫外线/降雨概率（这些数据语言无关）
    text += f" Wind {w['wind_speed_kmph']} km/h, UV {w['uv_index']}, precip {w['precip_chance']}%."

    if tomorrow_desc and w.get("tomorrow_max"):
        tomorrow_text = get("weather_text_tomorrow", lang).format(
            desc=tomorrow_desc, high=w["tomorrow_max"], low="?"
        )
        text += f" {tomorrow_text}"
    return text


if __name__ == "__main__":
    w = get_weather("Shanghai")
    print(weather_to_text(w))
