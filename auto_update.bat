@echo off
chcp 65001 >nul
echo ==========================================
echo   CarbSeek Insight 每周自动更新脚本
echo ==========================================
echo.

REM 设置工作目录（根据实际情况修改）
SET WORK_DIR=C:\Users\lipen\Documents\Kimi\Workspaces\carbseek\insight-update

REM 检查目录是否存在
IF NOT EXIST "%WORK_DIR%" (
    echo [错误] 工作目录不存在: %WORK_DIR%
    echo 请修改脚本中的 WORK_DIR 路径
    pause
    exit /b 1
)

cd /d "%WORK_DIR%"

echo [信息] 工作目录: %CD%
echo.

REM 步骤1: 执行 Python 自动更新
echo [步骤 1/4] 执行内容更新...
python scripts\auto_update.py
IF ERRORLEVEL 1 (
    echo [错误] 更新失败，请检查错误日志
    pause
    exit /b 1
)

echo.
echo [步骤 2/4] 检查 Git 状态...
git status --short

echo.
echo [步骤 3/4] 提交更改...
git add .
FOR /F "tokens=*" %%a IN ('python -c "import datetime; print(datetime.datetime.now().strftime('%%Y-%%m-%%d'))"') DO SET TODAY=%%a
git commit -m "auto-update: 情报驾驶舱周更 (%TODAY%)"

echo.
echo [步骤 4/4] 推送到 GitHub...
git push origin main
IF ERRORLEVEL 1 (
    echo [警告] 推送到 main 失败，尝试 master...
    git push origin master
)

echo.
echo ==========================================
echo   自动更新完成！
echo ==========================================
echo.
echo 访问地址: https://carbseek.github.io/carbseek-insight/
echo.

REM 记录日志
FOR /F "tokens=*" %%a IN ('python -c "import datetime; print(datetime.datetime.now().strftime('%%Y-%%m-%%d %%H:%%M:%%S'))"') DO SET NOW=%%a
echo [%NOW%] 自动更新完成 >> auto_update.log

REM 可选: 打开浏览器预览
REM start https://carbseek.github.io/carbseek-insight/
