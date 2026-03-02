@echo off
echo ============================================
echo  Building China Weather Finder .exe
echo ============================================
echo.

REM Install dependencies
echo [1/3] Installing dependencies...
pip install -r requirements.txt pyinstaller
echo.

REM Find streamlit package location for hidden imports and data
echo [2/3] Locating Streamlit package...
for /f "delims=" %%i in ('python -c "import streamlit; import os; print(os.path.dirname(streamlit.__file__))"') do set STREAMLIT_DIR=%%i
echo Found Streamlit at: %STREAMLIT_DIR%

echo.
echo [3/3] Building executable with PyInstaller...
pyinstaller ^
    --name "ChinaWeatherFinder" ^
    --onedir ^
    --windowed ^
    --add-data "app.py;." ^
    --add-data "china_cities.py;." ^
    --add-data "weather_api.py;." ^
    --add-data "%STREAMLIT_DIR%;streamlit" ^
    --hidden-import streamlit ^
    --hidden-import streamlit.web.cli ^
    --hidden-import streamlit.runtime.scriptrunner ^
    --hidden-import pandas ^
    --hidden-import requests ^
    --collect-all streamlit ^
    --noconfirm ^
    run.py

echo.
echo ============================================
if exist "dist\ChinaWeatherFinder" (
    echo  打包成功！
    echo  程序目录: dist\ChinaWeatherFinder\
    echo  可执行文件: dist\ChinaWeatherFinder\ChinaWeatherFinder.exe
    echo.
    echo  正在创建分发压缩包...
    powershell -Command "Compress-Archive -Path 'dist\ChinaWeatherFinder' -DestinationPath 'dist\ChinaWeatherFinder.zip' -Force"
    if exist "dist\ChinaWeatherFinder.zip" (
        echo  压缩包已生成: dist\ChinaWeatherFinder.zip
        echo.
        echo  ========== 分发说明 ==========
        echo  1. 将 dist\ChinaWeatherFinder.zip 发给对方
        echo  2. 对方解压整个文件夹
        echo  3. 双击 ChinaWeatherFinder.exe 运行
        echo  4. 浏览器打开 http://localhost:8501
        echo  注意：不要把 .exe 从文件夹中单独拿出，它依赖同目录下的文件！
    )
) else (
    echo  打包失败，请检查上方错误信息。
)
echo ============================================
pause
