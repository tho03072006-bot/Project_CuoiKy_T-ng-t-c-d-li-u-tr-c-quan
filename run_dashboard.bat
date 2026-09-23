@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" goto :setup
".venv\Scripts\python.exe" -m streamlit run dashboard/app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
exit /b %errorlevel%
:setup
echo Chua co moi truong. Chay setup.bat truoc.
pause
exit /b 1
