@echo off
chcp 65001 >nul
title VR眼球追踪平台 - 一键启动全部服务

echo.
echo =============================================
echo   VR眼球追踪数据可视化平台 - 一键启动
echo =============================================
echo.
echo 🎯 这将同时启动：
echo    ✅ 后端API服务器 (Flask - 8080端口)
echo    ✅ React前端应用 (3000端口)
echo.

set /p choice="选择启动模式 [1=React版本, 2=原版本, 3=同时启动]: "

if "%choice%"=="1" goto start_react
if "%choice%"=="2" goto start_original
if "%choice%"=="3" goto start_both
goto invalid

:start_react
echo.
echo 🚀 启动React版本...
echo.

echo 📡 启动后端API服务器...
start "后端API服务器" cmd /c "python start_server.py"

timeout /t 3 /nobreak >nul

echo 🎨 启动React前端...
start "React前端" cmd /c "cd frontend && npm start"

echo.
echo ✅ React版本启动完成！
echo 📍 访问地址: http://localhost:3000
echo 🔗 API地址: http://localhost:8080
goto end

:start_original
echo.
echo 🚀 启动原版本...
python start_server.py
goto end

:start_both
echo.
echo 🚀 同时启动两个版本...
echo.

echo 📡 启动后端API服务器...
start "后端API服务器" cmd /c "python start_server.py"

timeout /t 3 /nobreak >nul

echo 🎨 启动React前端...
start "React前端" cmd /c "cd frontend && npm start"

echo.
echo ✅ 两个版本都已启动！
echo 📍 React版本: http://localhost:3000
echo 📍 原版本: http://localhost:8080
goto end

:invalid
echo ❌ 无效选择，请输入 1、2 或 3
pause
exit /b 1

:end
echo.
echo 🎉 启动完成！
echo.
echo 💡 使用提示:
echo    - React版本: 现代化界面，开发体验更好
echo    - 原版本: 功能完整，稳定可靠
echo    - 两个版本共享同一个后端API
echo.
pause