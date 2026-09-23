@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
set "PROJECT_PY=.venv\Scripts\python.exe"
if not exist "%PROJECT_PY%" goto :setup
echo [1/5] Tien xu ly du lieu raw co san
"%PROJECT_PY%" scripts/pipeline_tien_xu_ly.py
if errorlevel 1 goto :err
echo [2/5] Tao SQLite
"%PROJECT_PY%" scripts/make_db.py
if errorlevel 1 goto :err
echo [3/5] Tao 10 hinh EDA
"%PROJECT_PY%" eda/eda_phan_tich.py
if errorlevel 1 goto :err
echo [4/5] Huan luyen va danh gia ngoai mau
"%PROJECT_PY%" models/du_bao.py
if errorlevel 1 goto :err
echo [5/5] Kiem tra dashboard
"%PROJECT_PY%" tests/verify_project.py
if errorlevel 1 goto :err
echo HOAN TAT. Chay run_dashboard.bat de mo demo.
pause
exit /b 0
:setup
echo Chay setup.bat truoc.
pause
exit /b 1
:err
echo CO LOI. Xem thong bao phia tren. Khong tiep tuc cac buoc sau.
pause
exit /b 1
