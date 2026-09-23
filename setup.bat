@echo off
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if exist ".venv\Scripts\python.exe" goto :install
python -m venv .venv
if errorlevel 1 goto :err
:install
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto :err
echo Cai dat xong. Chay run_dashboard.bat.
pause
exit /b 0
:err
echo Cai dat loi. Can Python 3.11 va ket noi mang de cai thu vien.
pause
exit /b 1
