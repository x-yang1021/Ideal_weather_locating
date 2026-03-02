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
    echo  Build successful!
    echo  Output: dist\ChinaWeatherFinder\ChinaWeatherFinder.exe
    echo.
    echo  To run: double-click ChinaWeatherFinder.exe
    echo  Then open http://localhost:8501 in your browser
) else (
    echo  Build failed. Check the output above for errors.
)
echo ============================================
pause
