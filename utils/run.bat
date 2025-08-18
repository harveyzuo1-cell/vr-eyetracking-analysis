@echo off
echo ========================================
echo VR眼球追踪数据处理工具
echo ========================================
echo.

echo 正在检查Python环境...
python --version
if errorlevel 1 (
    echo 错误：未找到Python，请确保Python已正确安装并添加到PATH环境变量中
    pause
    exit /b 1
)

echo.
echo 正在检查依赖包...
pip list | findstr numpy >nul
if errorlevel 1 (
    echo 正在安装缺失的依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误：依赖包安装失败
        pause
        exit /b 1
    )
)

echo.
echo 开始处理数据...
echo ========================================
python vr_eyetracking_processor.py

echo.
echo ========================================
echo 处理完成！按任意键退出...
pause 