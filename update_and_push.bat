@echo off
echo ============================================================
echo   Valuation River Chart - Auto Update and Publish
echo ============================================================
echo.
echo [INFO] Please make sure LSEG Workspace desktop app is running.
echo.

echo [1/4] Querying latest data from LSEG Workspace (query_all.py)...
python query_all.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to fetch data from LSEG Workspace.
    echo Make sure the LSEG Workspace desktop app is running and logged in.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [1.5/4] Querying latest SOX data from yfinance (query_yf_sox.py)...
python query_yf_sox.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to fetch data from yfinance.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/4] Calculating valuation river bands (plot_river.py)...
python plot_river.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to calculate river bands.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/4] Compiling datasets to data.js (compile_data.py)...
python compile_data.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to compile data.js.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo [4/4] Pushing updated data.js to GitHub...
git add data.js
git commit -m "Auto-update valuation data to latest week"
git push origin main
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to push data to GitHub.
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ============================================================
echo   Success! Web site will update in 1 minute.
echo ============================================================
echo.
pause
