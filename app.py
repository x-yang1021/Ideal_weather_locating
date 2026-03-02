"""
China Weather Forecast City Finder (中国天气预报城市筛选器)

Select provinces, set temperature/weather/date criteria,
and find cities with consecutive days matching your ideal weather.
"""

import streamlit as st
import pandas as pd
import time
from china_cities import PROVINCES_CITIES, PROVINCE_NAMES
from weather_api import (
    fetch_forecast, find_consecutive_matches,
    WEATHER_CATEGORIES,
)

st.set_page_config(page_title="理想天气城市筛选器", page_icon="🌤️", layout="wide")
st.title("理想天气城市筛选器")
st.caption("China Ideal Weather City Finder — 找到未来10天符合你理想天气的城市")

# --- Sidebar: Province Selection ---
st.sidebar.header("1. 选择省份 (Select Provinces)")

# Quick select buttons
col1, col2 = st.sidebar.columns(2)
if col1.button("全选 (Select All)"):
    st.session_state["selected_provinces"] = PROVINCE_NAMES.copy()
if col2.button("清空 (Clear)"):
    st.session_state["selected_provinces"] = []

selected_provinces = st.sidebar.multiselect(
    "选择省份",
    PROVINCE_NAMES,
    default=st.session_state.get("selected_provinces", []),
    key="selected_provinces",
)

# Show city count
total_cities = sum(
    len(PROVINCES_CITIES[p]) for p in selected_provinces
)
st.sidebar.info(f"已选 {len(selected_provinces)} 个省份，共 {total_cities} 个城市")

# --- Sidebar: Filter Criteria ---
st.sidebar.header("2. 筛选条件 (Filter Criteria)")

min_consecutive = st.sidebar.slider(
    "最少连续天数 (Min consecutive days)",
    min_value=1, max_value=10, value=3,
)

temp_range = st.sidebar.slider(
    "温度范围 °C (Temperature range)",
    min_value=-40, max_value=50, value=(10, 20),
)

weather_filters = st.sidebar.multiselect(
    "天气条件 (Weather conditions) — 留空则不限",
    list(WEATHER_CATEGORIES.keys()),
    default=[],
)

# --- Sidebar: API Settings ---
st.sidebar.header("3. API 设置 (API Settings)")
api_provider = st.sidebar.radio(
    "天气数据源",
    ["Open-Meteo (免费，无需密钥)", "QWeather 和风天气 (需要API Key)"],
    index=0,
)

qweather_key = ""
if "QWeather" in api_provider:
    qweather_key = st.sidebar.text_input(
        "QWeather API Key",
        type="password",
        help="在 https://dev.qweather.com 注册获取免费API Key",
    )

provider_code = "qweather" if "QWeather" in api_provider else "open_meteo"

# --- Main Area: Run Search ---
if st.button("🔍 开始搜索 (Search)", type="primary", use_container_width=True):
    if not selected_provinces:
        st.warning("请先选择至少一个省份")
    elif "QWeather" in api_provider and not qweather_key:
        st.warning("请输入 QWeather API Key")
    else:
        qualifying_cities = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        city_index = 0
        for province in selected_provinces:
            cities = PROVINCES_CITIES[province]
            for city_cn, city_en, lat, lon in cities:
                city_index += 1
                progress_bar.progress(city_index / total_cities)
                status_text.text(
                    f"正在查询 {city_cn} ({city_index}/{total_cities})..."
                )

                forecast = fetch_forecast(
                    lat, lon, days=10,
                    api_provider=provider_code,
                    api_key=qweather_key,
                )

                if forecast is None:
                    continue

                result = find_consecutive_matches(
                    forecast,
                    temp_min=temp_range[0],
                    temp_max=temp_range[1],
                    weather_filters=weather_filters,
                    min_consecutive_days=min_consecutive,
                )

                if result["qualifies"]:
                    qualifying_cities.append({
                        "省份": province,
                        "城市": city_cn,
                        "City": city_en,
                        "连续天数": result["best_run_days"],
                        "开始日期": result["best_run_start"],
                        "结束日期": result["best_run_end"],
                        "forecast_detail": result["matching_forecast"],
                    })

                # Rate limiting: be polite to the API
                time.sleep(0.3)

        progress_bar.progress(1.0)
        status_text.text(f"搜索完成！共查询 {total_cities} 个城市")

        # --- Display Results ---
        st.header(f"搜索结果：{len(qualifying_cities)} 个城市符合条件")

        if qualifying_cities:
            # Summary table
            df = pd.DataFrame([
                {
                    "省份": c["省份"],
                    "城市": c["城市"],
                    "City": c["City"],
                    "最长连续天数": c["连续天数"],
                    "开始日期": c["开始日期"],
                    "结束日期": c["结束日期"],
                }
                for c in qualifying_cities
            ])
            df = df.sort_values("最长连续天数", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Detailed forecast per city
            st.subheader("详细预报 (Detailed Forecast)")
            for city in qualifying_cities:
                with st.expander(
                    f"{city['城市']} ({city['City']}) — "
                    f"{city['连续天数']} 天 "
                    f"({city['开始日期']} ~ {city['结束日期']})"
                ):
                    detail_df = pd.DataFrame([
                        {
                            "日期": d["date"],
                            "最低温°C": d["temp_min"],
                            "最高温°C": d["temp_max"],
                            "天气": d["weather_text"],
                        }
                        for d in city["forecast_detail"]
                    ])
                    st.dataframe(detail_df, use_container_width=True, hide_index=True)
        else:
            st.info(
                "没有找到符合条件的城市。\n\n"
                "建议：放宽温度范围、减少连续天数要求，或选择更多省份。"
            )
