# 理想天气城市筛选器 (China Ideal Weather City Finder)

选择中国省份，设置温度、天气和连续天数条件，找到未来10天内符合你理想天气的城市。

## 安装 (Install)

```bash
pip install -r requirements.txt
```

## 运行 (Run)

```bash
streamlit run app.py
```

## 使用说明 (Usage)

1. **选择省份** — 在左侧勾选你感兴趣的省份
2. **设置条件** — 设置温度范围、天气条件、最少连续天数
3. **点击搜索** — 查看符合条件的城市列表和详细预报

## 打包为 Windows .exe (Build Windows Executable)

在 Windows 上运行：

```bat
build.bat
```

生成的程序在 `dist\ChinaWeatherFinder\` 目录下，双击 `ChinaWeatherFinder.exe` 即可运行，然后在浏览器打开 http://localhost:8501 。

## 天气数据源 (Weather API)

- **Open-Meteo** (默认): 免费，无需API Key，支持16天预报
- **QWeather 和风天气**: 需要在 https://dev.qweather.com 注册获取免费API Key
