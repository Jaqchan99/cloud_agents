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
        uv_index = int(curr.get("uvIndex", 0))

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


def weather_to_text(w: dict) -> str:
    """将天气数据转为给 AI 使用的描述文本"""
    if not w.get("success"):
        return "天气数据暂时无法获取。"

    desc_map = {
        "Sunny": "晴天", "Clear": "晴朗", "Partly cloudy": "多云",
        "Cloudy": "阴天", "Overcast": "阴转多云", "Mist": "有雾",
        "Fog": "有雾", "Freezing fog": "冻雾",
        "Light rain": "小雨", "Moderate rain": "中雨", "Heavy rain": "大雨",
        "Light drizzle": "小毛毛雨", "Freezing drizzle": "冻雨",
        "Light snow": "小雪", "Moderate snow": "中雪", "Heavy snow": "大雪",
        "Thundery outbreaks possible": "雷阵雨", "Patchy thunder possible": "局部雷阵雨",
        "Blizzard": "暴雪", "Patchy rain possible": "局部有雨",
        "Blowing snow": "暴风雪", "Ice pellets": "冰雹",
        "Light sleet": "小雨夹雪", "Moderate or heavy sleet": "雨夹雪",
        "Patchy light rain": "局部小雨", "Patchy light snow": "局部小雪",
    }
    desc_cn = desc_map.get(w["description"], w["description"])
    tomorrow_cn = desc_map.get(w.get("tomorrow_desc", ""), w.get("tomorrow_desc", ""))

    text = (
        f"当前天气：{desc_cn}，气温 {w['temp_c']}°C（体感 {w['feels_like']}°C），"
        f"今日 {w['today_min']}~{w['today_max']}°C，湿度 {w['humidity']}%，"
        f"风速 {w['wind_speed_kmph']} km/h，紫外线指数 {w['uv_index']}，"
        f"降雨概率 {w['precip_chance']}%。"
    )
    if tomorrow_cn and w.get("tomorrow_max"):
        text += f"明日预报：{tomorrow_cn}，最高 {w['tomorrow_max']}°C。"
    return text


if __name__ == "__main__":
    w = get_weather("Shanghai")
    print(weather_to_text(w))
