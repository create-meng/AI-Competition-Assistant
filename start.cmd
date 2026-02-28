@echo off
setlocal EnableExtensions

rem Usage:
rem   start.cmd                 -> start backend + frontend
rem   start.cmd initdb          -> init db then start backend + frontend
rem   start.cmd jishe 8000 3000 -> custom env/backendPort/frontendPort
rem   start.cmd initdb jishe 8000 3000

set "INITDB=0"
set "CONDA_ENV=jishe"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3000"

if /I "%~1"=="initdb" (
  set "INITDB=1"
  shift
)

if not "%~1"=="" set "CONDA_ENV=%~1"
if not "%~2"=="" set "BACKEND_PORT=%~2"
if not "%~3"=="" set "FRONTEND_PORT=%~3"

set "REPO_ROOT=%~dp0"
set "BACKEND_DIR=%REPO_ROOT%backend"
set "FRONTEND_DIR=%REPO_ROOT%frontend"

if not exist "%BACKEND_DIR%" (
  echo 未找到 backend 目录: "%BACKEND_DIR%"
  exit /b 1
)
if not exist "%FRONTEND_DIR%" (
  echo 未找到 frontend 目录: "%FRONTEND_DIR%"
  exit /b 1
)

where conda >nul 2>nul
if errorlevel 1 (
  echo 找不到 conda。请先安装并确保已加入 PATH。
  exit /b 1
)
where npm >nul 2>nul
if errorlevel 1 (
  echo 找不到 npm。请先安装 Node.js 并确保 npm 已加入 PATH。
  exit /b 1
)

echo 启动后端: http://localhost:%BACKEND_PORT%
echo 启动前端: http://localhost:%FRONTEND_PORT%

if "%INITDB%"=="1" (
  echo 初始化数据库...
  pushd "%BACKEND_DIR%" >nul
  conda run --no-capture-output -n "%CONDA_ENV%" python scripts\init_db.py
  if errorlevel 1 (
    popd >nul
    echo 数据库初始化失败。
    exit /b 1
  )
  popd >nul
)

start "Backend" cmd /k "cd /d ""%BACKEND_DIR%"" && echo [Backend] conda run --no-capture-output -n ""%CONDA_ENV%"" python -m uvicorn main:app --reload --host 0.0.0.0 --port %BACKEND_PORT% && conda run --no-capture-output -n ""%CONDA_ENV%"" python -m uvicorn main:app --reload --host 0.0.0.0 --port %BACKEND_PORT% || (echo 后端启动失败 & pause)"
start "Frontend" cmd /k "cd /d ""%FRONTEND_DIR%"" && npm run dev -- --port %FRONTEND_PORT%"

endlocal
