@echo off
chcp 65001 >nul
title React前端启动

echo.
echo ========================================
echo   VR眼球追踪平台 - React前端启动
echo ========================================
echo.

echo 检查Node.js环境...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未检测到Node.js，请先安装Node.js
    echo 下载地址: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js版本:
node --version

echo.
echo 检查npm环境...
npm --version >nul 2>&1
if errorlevel 1 (
    echo ❌ npm不可用
    pause
    exit /b 1
)

echo ✅ npm版本:
npm --version

echo.
echo 检查依赖安装...
if not exist "node_modules" (
    echo 📦 首次运行，正在安装依赖...
    npm install
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo ✅ 依赖已安装
)

echo.
echo 🚀 启动React开发服务器...
echo 📍 前端地址: http://localhost:3000
echo 🔗 API代理: http://localhost:8080
echo.
echo ⚠️  请确保后端服务器已启动 (运行根目录的 启动服务器.bat)
echo.

npm start

pause