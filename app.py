"""
中国天气预报城市筛选器

选择省份，设置温度、天气和连续天数条件，找到未来10天内符合理想天气的城市。
支持两种模式：严格连续模式和灵活窗口模式（n-in-m）。
"""

import streamlit as st
import pandas as pd
import time
from china_cities import PROVINCES_CITIES, PROVINCE_NAMES
from weather_api import (
    fetch_forecast, find_consecutive_matches, find_n_in_m_matches,
    WEATHER_CATEGORIES,
)

st.set_page_config(page_title="理想天气城市筛选器", page_icon="🌤️", layout="wide")
st.title("理想天气城市筛选器")
st.caption("找到未来10天符合你理想天气的城市")

# --- 侧边栏：省份选择 ---
st.sidebar.header("1. 选择省份")

col1, col2 = st.sidebar.columns(2)
if col1.button("全选"):
    st.session_state["selected_provinces"] = PROVINCE_NAMES.copy()
if col2.button("清空"):
    st.session_state["selected_provinces"] = []

selected_provinces = st.sidebar.multiselect(
    "选择省份",
    PROVINCE_NAMES,
    default=st.session_state.get("selected_provinces", []),
    key="selected_provinces",
)

total_cities = sum(
    len(PROVINCES_CITIES[p]) for p in selected_provinces
)
st.sidebar.info(f"已选 {len(selected_provinces)} 个省份，共 {total_cities} 个城市")

# --- 侧边栏：筛选条件 ---
st.sidebar.header("2. 筛选条件")

filter_mode = st.sidebar.radio(
    "筛选模式",
    ["灵活模式（M天内至少N天符合）", "严格模式（连续N天全部符合）"],
    index=0,
    help="灵活模式更实用：例如6天内至少3天晴天。严格模式要求每一天都符合条件。",
)

if "灵活" in filter_mode:
    window_size = st.sidebar.slider(
        "窗口天数 (M)",
        min_value=2, max_value=10, value=6,
        help="在连续M天的窗口内统计",
    )
    min_good_days = st.sidebar.slider(
        "最少好天气天数 (N)",
        min_value=1, max_value=10, value=3,
        help="窗口内至少N天符合条件",
    )
    if min_good_days > window_size:
        st.sidebar.warning("N 不能大于 M，已自动调整")
        min_good_days = window_size
else:
    min_consecutive = st.sidebar.slider(
        "最少连续天数",
        min_value=1, max_value=10, value=3,
    )

temp_range = st.sidebar.slider(
    "温度范围 (°C)",
    min_value=-40, max_value=50, value=(10, 20),
)

weather_filters = st.sidebar.multiselect(
    "天气条件（留空则不限）",
    list(WEATHER_CATEGORIES.keys()),
    default=[],
)

# --- 侧边栏：数据源设置 ---
st.sidebar.header("3. 天气数据源")
api_provider = st.sidebar.radio(
    "选择数据源",
    ["Open-Meteo（免费，无需密钥）", "和风天气（需要密钥）"],
    index=0,
)

qweather_key = ""
if "和风天气" in api_provider:
    qweather_key = st.sidebar.text_input(
        "和风天气 API 密钥",
        type="password",
        help="在 https://dev.qweather.com 注册获取免费密钥",
    )

provider_code = "qweather" if "和风天气" in api_provider else "open_meteo"

# --- 主区域：执行搜索 ---
if st.button("🔍 开始搜索", type="primary", use_container_width=True):
    if not selected_provinces:
        st.warning("请先选择至少一个省份")
    elif "和风天气" in api_provider and not qweather_key:
        st.warning("请输入和风天气 API 密钥")
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
                    f"正在查询 {city_cn}（{city_index}/{total_cities}）..."
                )

                forecast = fetch_forecast(
                    lat, lon, days=10,
                    api_provider=provider_code,
                    api_key=qweather_key,
                )

                if forecast is None:
                    continue

                if "灵活" in filter_mode:
                    result = find_n_in_m_matches(
                        forecast,
                        temp_min=temp_range[0],
                        temp_max=temp_range[1],
                        weather_filters=weather_filters,
                        min_good_days=min_good_days,
                        window_size=window_size,
                    )
                    if result["qualifies"]:
                        qualifying_cities.append({
                            "省份": province,
                            "城市": city_cn,
                            "好天气天数": result["good_days"],
                            "窗口天数": window_size,
                            "开始日期": result["window_start"],
                            "结束日期": result["window_end"],
                            "forecast_detail": result["window_forecast"],
                        })
                else:
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
                            "好天气天数": result["best_run_days"],
                            "窗口天数": result["best_run_days"],
                            "开始日期": result["best_run_start"],
                            "结束日期": result["best_run_end"],
                            "forecast_detail": result["matching_forecast"],
                        })

                # 限速：避免请求过快
                time.sleep(0.3)

        progress_bar.progress(1.0)
        status_text.text(f"搜索完成！共查询 {total_cities} 个城市")

        # --- 显示结果 ---
        st.header(f"搜索结果：{len(qualifying_cities)} 个城市符合条件")

        if qualifying_cities:
            if "灵活" in filter_mode:
                df = pd.DataFrame([
                    {
                        "省份": c["省份"],
                        "城市": c["城市"],
                        "好天气天数": f"{c['好天气天数']}/{c['窗口天数']}",
                        "开始日期": c["开始日期"],
                        "结束日期": c["结束日期"],
                    }
                    for c in qualifying_cities
                ])
                df = df.sort_values("好天气天数", ascending=False)
            else:
                df = pd.DataFrame([
                    {
                        "省份": c["省份"],
                        "城市": c["城市"],
                        "最长连续天数": c["好天气天数"],
                        "开始日期": c["开始日期"],
                        "结束日期": c["结束日期"],
                    }
                    for c in qualifying_cities
                ])
                df = df.sort_values("最长连续天数", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 各城市详细预报
            st.subheader("详细预报")
            for city in qualifying_cities:
                label = (
                    f"{city['城市']} — "
                    f"{city['好天气天数']}/{city['窗口天数']} 天"
                    f"（{city['开始日期']} ~ {city['结束日期']}）"
                )
                with st.expander(label):
                    rows = []
                    for d in city["forecast_detail"]:
                        row = {
                            "日期": d["date"],
                            "最低温(°C)": d["temp_min"],
                            "最高温(°C)": d["temp_max"],
                            "天气": d["weather_text"],
                        }
                        if "matches" in d:
                            row["符合"] = "✅" if d["matches"] else "❌"
                        rows.append(row)
                    detail_df = pd.DataFrame(rows)
                    st.dataframe(detail_df, use_container_width=True, hide_index=True)
        else:
            st.info(
                "没有找到符合条件的城市。\n\n"
                "建议：放宽温度范围、减少好天气天数要求，或选择更多省份。"
            )
