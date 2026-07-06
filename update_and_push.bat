@echo off
setlocal EnableExtensions

set "PROJECT_DIR=C:\Users\USER\Documents\Analysis\sox-pe-river-latest"
set "PYTHON_EXE=C:\Users\USER\AppData\Local\Python\pythoncore-3.14-64\python.exe"
set "GH_EXE=C:\Users\USER\Documents\Analysis\.tools\bin\gh.exe"
set "REPO=Wiimandy/sox-pe-river"
set "BRANCH=main"

echo ============================================================
echo   SOX PE River - LSEG/yfinance Proxy Update and Publish
echo ============================================================
echo.
echo [INFO] SOX source policy:
echo [INFO] LSEG through 2026-07-06; yfinance proxy from 2026-07-07 onward.
echo.

cd /d "%PROJECT_DIR%"
if %errorlevel% neq 0 (
    echo [ERROR] Failed to enter project folder:
    echo         %PROJECT_DIR%
    pause
    exit /b %errorlevel%
)

echo [1/5] Updating SOX daily tracking log...
"%PYTHON_EXE%" record_daily_tracking.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to update SOX daily tracking log.
    pause
    exit /b %errorlevel%
)

echo.
echo [2/5] Splicing SOX source series...
"%PYTHON_EXE%" splice_sox_yfinance_proxy.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to splice SOX yfinance proxy data.
    pause
    exit /b %errorlevel%
)

echo.
echo [3/5] Calculating valuation river bands...
"%PYTHON_EXE%" plot_river.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to calculate river bands.
    pause
    exit /b %errorlevel%
)

echo.
echo [4/5] Compiling datasets to data.js...
"%PYTHON_EXE%" compile_data.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to compile data.js.
    pause
    exit /b %errorlevel%
)

echo.
echo [5/5] Publishing data.js and scripts to GitHub...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $gh=$env:GH_EXE; $repo=$env:REPO; $branch=$env:BRANCH; $files=@('data.js','index.html','app.js','compile_data.py','plot_river.py','splice_sox_yfinance_proxy.py','sox_pe_data_W.csv','sox_pe_river_data_W.csv'); foreach($file in $files){ if(Test-Path $file){ Write-Host \"Uploading $file\"; $sha=& $gh api \"repos/$repo/contents/$file\" --jq '.sha' 2>$null; $content=[Convert]::ToBase64String([IO.File]::ReadAllBytes($file)); $body=@{message='Auto-update SOX LSEG/yfinance proxy data'; content=$content; branch=$branch} ; if($sha){ $body.sha=$sha }; $body=$body | ConvertTo-Json -Compress; $body | & $gh api \"repos/$repo/contents/$file\" -X PUT --input - | Out-Null } }"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Failed to upload files to GitHub.
    pause
    exit /b %errorlevel%
)

echo.
echo ============================================================
echo   Success. GitHub Pages should refresh shortly.
echo ============================================================
echo.
pause
