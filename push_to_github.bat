@echo off
chcp 65001 >nul
echo ==========================================
echo   CarbSeek Insight 推送到 GitHub
echo ==========================================
echo.

REM 确保在正确的目录
cd /d "%~dp0"

echo [信息] 当前目录: %CD%
echo.

REM 检查 Git 状态
echo [步骤 1/3] 检查 Git 状态...
git status --short

echo.
echo [步骤 2/3] 添加所有更改...
git add -A

FOR /F "tokens=*" %%a IN ('python -c "import datetime; print(datetime.datetime.now().strftime('%%Y-%%m-%%d %%H:%%M'))"') DO SET NOW=%%a
git commit -m "deploy: 自动更新系统 + 情报驾驶舱 (%NOW%)" 2>nul

echo.
echo [步骤 3/3] 推送到 GitHub...
echo.
echo 正在推送...如果提示输入用户名密码，请输入您的 GitHub 凭据
echo.

REM 尝试推送到 main
git push origin master:main --force

IF ERRORLEVEL 1 (
    echo.
    echo [错误] 推送失败，尝试其他方式...
    echo.
    echo 请手动在 Git Bash 中执行以下命令：
    echo   cd "%CD%"
    echo   git push origin master:main --force
    echo.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo   推送成功！
echo ==========================================
echo.
echo 访问地址: https://carbseek.github.io/carbseek-insight/
echo.
pause
