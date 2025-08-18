@echo off
chcp 65001 >nul
title VR眼动数据分析系统

echo.
echo =====================================
echo   VR眼动数据分析系统 - 一键启动
echo =====================================
echo.

python start_server.py

pause 