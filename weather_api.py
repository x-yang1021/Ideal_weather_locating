"""
Weather forecast fetching module.
Supports Open-Meteo (free, no API key) and QWeather (needs API key).
"""

import requests
from datetime import datetime, timedelta
from typing import Optional

# WMO Weather interpretation codes -> human-readable conditions
WMO_CODES = {
    0: "晴",
    1: "晴",
    2: "多云",
    3: "阴",
    45: "雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    56: "冻毛毛雨",
    57: "冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "阵雨",
    82: "大阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴冰雹",
    99: "雷暴冰雹",
}

# Simplified weather categories for filtering
WEATHER_CATEGORIES = {
    "晴": [0, 1],
    "多云/阴": [2, 3],
    "雾": [45, 48],
    "雨": [51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82],
    "雪": [71, 73, 75, 77, 85, 86],
    "雷暴": [95, 96, 99],
}


def fetch_open_meteo(lat: float, lon: float, days: int = 10) -> Optional[list[dict]]:
    """
    Fetch daily forecast from Open-Meteo API.
    Returns list of dicts with keys: date, temp_min, temp_max, weather_code, weather_text
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "forecast_days": min(days, 16),
        "timezone": "Asia/Shanghai",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        daily = data["daily"]
        results = []
        for i in range(len(daily["time"])):
            code = daily["weather_code"][i]
            results.append({
                "date": daily["time"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "temp_max": daily["temperature_2m_max"][i],
                "weather_code": code,
                "weather_text": WMO_CODES.get(code, f"未知({code})"),
            })
        return results
    except Exception as e:
        print(f"Open-Meteo error: {e}")
        return None


def fetch_qweather(lat: float, lon: float, api_key: str, days: int = 10) -> Optional[list[dict]]:
    """
    Fetch daily forecast from QWeather (和风天气) API.
    Free tier supports up to 7 days. Paid supports 10/15/30.
    """
    day_param = "7d" if days <= 7 else "10d"
    url = f"https://devapi.qweather.com/v7/weather/{day_param}"
    params = {
        "location": f"{lon:.2f},{lat:.2f}",
        "key": api_key,
        "lang": "zh",
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "200":
            print(f"QWeather error code: {data.get('code')}")
            return None
        results = []
        for day in data["daily"]:
            results.append({
                "date": day["fxDate"],
                "temp_min": float(day["tempMin"]),
                "temp_max": float(day["tempMax"]),
                "weather_code": -1,
                "weather_text": f"{day['textDay']}",
            })
        return results
    except Exception as e:
        print(f"QWeather error: {e}")
        return None


def fetch_forecast(lat: float, lon: float, days: int = 10,
                   api_provider: str = "open_meteo",
                   api_key: str = "") -> Optional[list[dict]]:
    """Fetch forecast using the selected provider."""
    if api_provider == "qweather" and api_key:
        return fetch_qweather(lat, lon, api_key, days)
    return fetch_open_meteo(lat, lon, days)


def matches_weather_filter(weather_code: int, weather_text: str,
                           selected_categories: list[str]) -> bool:
    """Check if a day's weather matches any of the selected filter categories."""
    if not selected_categories:
        return True
    for cat in selected_categories:
        if cat in WEATHER_CATEGORIES:
            if weather_code in WEATHER_CATEGORIES[cat]:
                return True
        # Also do text-based matching for QWeather results
        cat_chinese = cat.split("(")[0].strip()
        if cat_chinese and cat_chinese in weather_text:
            return True
    return False


def find_consecutive_matches(forecast: list[dict],
                             temp_min: float, temp_max: float,
                             weather_filters: list[str],
                             min_consecutive_days: int) -> list[dict]:
    """
    Find stretches of consecutive days that meet temperature and weather criteria.
    Returns the matching day ranges.
    """
    matching_days = []
    for day in forecast:
        temp_ok = day["temp_min"] >= temp_min and day["temp_max"] <= temp_max
        weather_ok = matches_weather_filter(
            day["weather_code"], day["weather_text"], weather_filters
        )
        matching_days.append(temp_ok and weather_ok)

    # Find consecutive runs
    best_run_start = -1
    best_run_len = 0
    current_start = -1
    current_len = 0
    runs = []

    for i, match in enumerate(matching_days):
        if match:
            if current_start == -1:
                current_start = i
                current_len = 1
            else:
                current_len += 1
        else:
            if current_len >= min_consecutive_days:
                runs.append((current_start, current_len))
            if current_len > best_run_len:
                best_run_len = current_len
                best_run_start = current_start
            current_start = -1
            current_len = 0

    # Handle run at end
    if current_len >= min_consecutive_days:
        runs.append((current_start, current_len))
    if current_len > best_run_len:
        best_run_len = current_len
        best_run_start = current_start

    if best_run_len >= min_consecutive_days:
        return {
            "qualifies": True,
            "best_run_days": best_run_len,
            "best_run_start": forecast[best_run_start]["date"],
            "best_run_end": forecast[best_run_start + best_run_len - 1]["date"],
            "all_runs": runs,
            "matching_forecast": [
                forecast[i] for i in range(best_run_start, best_run_start + best_run_len)
            ],
        }
    return {"qualifies": False, "best_run_days": best_run_len}
