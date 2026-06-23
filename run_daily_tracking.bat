@echo off
:: Change working directory to the folder containing this batch file
cd /d "%~dp0"

:: Run the daily tracking script and append logs to daily_tracking_cron.log
python record_daily_tracking.py >> daily_tracking_cron.log 2>&1
