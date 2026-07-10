@echo off
chcp 65001 >nul
echo ==========================================
echo   CarbSeek Insight 一键部署脚本
echo ==========================================
echo.

REM 检查是否已设置远程仓库
FOR /F "tokens=*" %%a IN ('git remote get-url origin 2^>nul') DO SET REMOTE_URL=%%a

IF "%REMOTE_URL%"=="" (
    echo [提示] 尚未配置 GitHub 远程仓库
    echo.
    echo 请先在 GitHub 创建一个公开仓库：
    echo   1. 打开 https://github.com/new
    echo   2. Repository name: carbseek-insight
    echo   3. 选择 Public
    echo   4. 点击 Create repository
    echo.
    set /p GITHUB_USER=请输入你的 GitHub 用户名: 
    git remote add origin https://github.com/%GITHUB_USER%/carbseek-insight.git
    echo [完成] 已添加远程仓库
) ELSE (
    echo [信息] 远程仓库: %REMOTE_URL%
)

echo.
echo [步骤 1/3] 推送代码到 GitHub...
git add .
git commit -m "deploy: update intelligence dashboard" 2>nul
git push -u origin main 2>nul || git push -u origin master 2>nul

echo.
echo [步骤 2/3] 等待 GitHub Actions 部署...
echo   部署通常需要 1-2 分钟

FOR /F "tokens=*" %%a IN ('git remote get-url origin 2^>nul') DO SET REMOTE_URL=%%a
FOR /F "tokens=4 delims=/" %%a IN ("%REMOTE_URL%") DO SET REPO_NAME=%%a
FOR /F "tokens=3 delims=/" %%a IN ("%REMOTE_URL%") DO SET USER_NAME=%%a

echo.
echo ==========================================
echo   部署完成！
echo ==========================================
echo.
echo 你的情报驾驶舱已上线：
echo   https://%USER_NAME%.github.io/%REPO_NAME%/
echo.
echo 如果页面未显示，请检查：
echo   1. GitHub 仓库是否设为 Public
echo   2. Settings -^> Pages -^> Source 是否设为 GitHub Actions
echo.
pause
