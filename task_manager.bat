@echo off
chcp 65001 >nul
echo ==========================================
echo   CarbSeek Insight 定时任务管理
echo ==========================================
echo.
echo 选择操作:
echo   [1] 安装定时任务（每周一 9:00 自动更新）
echo   [2] 立即手动运行更新
echo   [3] 查看任务状态
echo   [4] 删除定时任务
echo   [5] 退出
echo.
set /p choice=请输入选项 (1-5): 

if "%choice%"=="1" goto install
if "%choice%"=="2" goto run_now
if "%choice%"=="3" goto status
if "%choice%"=="4" goto remove
if "%choice%"=="5" goto end

echo [错误] 无效选项
goto end

:install
echo.
echo [安装] 正在创建定时任务...
echo 需要管理员权限，请确认 UAC 弹窗...
powershell -ExecutionPolicy Bypass -File setup_task.ps1
pause
goto end

:run_now
echo.
echo [执行] 立即运行更新...
call auto_update.bat
pause
goto end

:status
echo.
echo [状态] 查看定时任务...
powershell -Command "Get-ScheduledTask -TaskName 'CarbSeekInsight*' | Select-Object TaskName, State, NextRunTime | Format-Table"
pause
goto end

:remove
echo.
echo [删除] 正在删除定时任务...
powershell -Command "Unregister-ScheduledTask -TaskName 'CarbSeekInsight_WeeklyUpdate' -Confirm:$false"
echo [完成] 任务已删除
pause
goto end

:end
echo.
echo 按任意键退出...
pause >nul
