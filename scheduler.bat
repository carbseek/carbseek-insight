@echo off
chcp 65001 >nul
echo ==========================================
echo   CarbSeek Intelligence 定时任务管理器
echo ==========================================
echo.
echo  执行计划: 每周一 + 每周五 上午 10:00
echo  执行内容: 情报采集 ^> 生成Dashboard ^> 推送到GitHub
echo.
echo 请选择操作:
echo.
echo   [1] 安装定时任务（需要管理员权限）
echo   [2] 立即手动运行更新
echo   [3] 查看任务状态和下次执行时间
echo   [4] 查看最近执行日志
echo   [5] 删除定时任务
echo   [6] 退出
echo.
set /p choice=请输入选项 (1-6): 

if "%choice%"=="1" goto install
if "%choice%"=="2" goto run_now
if "%choice%"=="3" goto status
if "%choice%"=="4" goto logs
if "%choice%"=="5" goto remove
if "%choice%"=="6" goto end

echo [错误] 无效选项，请重新运行
goto end

:install
echo.
echo [安装] 正在创建定时任务...
echo 注意：需要管理员权限，请确认 UAC 弹窗...
echo.
powershell -ExecutionPolicy Bypass -File setup_schedule.ps1
echo.
pause
goto end

:run_now
echo.
echo [执行] 立即运行完整更新流水线...
echo 工作目录: carbseek-intelligence
echo.
cd /d "%~dp0"

echo [1/4] 执行情报采集...
python orchestrator.py

echo [2/4] 生成Dashboard...
python generate_dashboard.py

echo [3/4] 同步到GitHub仓库...
copy /y web\index.html ..\insight-update\intelligence.html
cd ..\insight-update
git add intelligence.html
git commit -m "auto-update: 情报中心手动更新 %date%"

echo [4/4] 推送到GitHub...
git push origin master:main --force

echo.
echo [完成] 手动更新完成！
echo 访问: https://carbseek.github.io/carbseek-insight/intelligence.html
echo.
pause
goto end

:status
echo.
echo [状态] 查看定时任务...
powershell -Command "Get-ScheduledTask -TaskName 'CarbSeekIntelligence*' | Get-ScheduledTaskInfo | Select-Object TaskName, State, NextRunTime, LastRunTime | Format-Table -AutoSize"
echo.
echo 如果显示空白，说明任务尚未安装，请选择 [1] 安装
echo.
pause
goto end

:logs
echo.
echo [日志] 最近执行记录...
if exist auto_run.log (
    echo === 最后30行日志 ===
    powershell -Command "Get-Content auto_run.log -Tail 30"
) else (
    echo 暂无日志文件，请先执行一次更新
echo.
pause
goto end

:remove
echo.
echo [删除] 正在删除定时任务...
powershell -Command "Unregister-ScheduledTask -TaskName 'CarbSeekIntelligence_AutoUpdate' -Confirm:$false 2>$null; Write-Host '任务已删除' -ForegroundColor Green"
echo.
pause
goto end

:end
echo.
echo 感谢使用 CarbSeek Intelligence
echo.
