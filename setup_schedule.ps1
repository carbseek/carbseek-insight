# CarbSeek Intelligence - 定时任务配置脚本
# ==========================================
# 配置：每周一和每周五 上午10:00 自动更新
# 用法：以管理员身份运行 PowerShell，执行: .\setup_schedule.ps1
# ==========================================

$TaskName = "CarbSeekIntelligence_AutoUpdate"
$TaskDescription = "CarbSeek Intelligence 情报中心自动更新 - 每周一/五 10:00执行"

# 工作目录和脚本路径
$WorkDir = "C:\Users\lipen\Documents\Kimi\Workspaces\carbseek\carbseek-intelligence"
$PythonExe = "python"

# 检查目录
if (-not (Test-Path $WorkDir)) {
    Write-Host "[错误] 工作目录不存在: $WorkDir" -ForegroundColor Red
    Write-Host "请修改脚本中的 WorkDir 路径" -ForegroundColor Yellow
    exit 1
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  CarbSeek Intelligence 定时任务配置" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "任务名称: $TaskName" -ForegroundColor White
Write-Host "执行时间: 每周一 10:00 + 每周五 10:00" -ForegroundColor White
Write-Host "工作目录: $WorkDir" -ForegroundColor White
Write-Host ""

# 删除已有任务
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[提示] 发现已有任务，先删除旧任务..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "[完成] 旧任务已删除" -ForegroundColor Green
}

# 创建触发器：每周一 10:00
$TriggerMonday = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "10:00"
# 创建触发器：每周五 10:00
$TriggerFriday = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Friday -At "10:00"

# 组合触发器
$Triggers = @($TriggerMonday, $TriggerFriday)

# 创建操作：执行完整流水线
# 执行顺序：1.采集情报 2.生成Dashboard 3.复制到insight-update 4.推送到GitHub
$ActionScript = @"
cd /d "$WorkDir"
echo ========================================== > auto_run.log
echo [CarbSeek Intelligence] 自动更新开始 >> auto_run.log
echo 时间: %date% %time% >> auto_run.log
echo ========================================== >> auto_run.log

echo [1/4] 执行情报采集... >> auto_run.log
python orchestrator.py >> auto_run.log 2>&1

echo [2/4] 生成Dashboard... >> auto_run.log
python generate_dashboard.py >> auto_run.log 2>&1

echo [3/4] 同步到GitHub仓库... >> auto_run.log
copy /y web\index.html ..\insight-update\intelligence.html >> auto_run.log
cd ..\insight-update
git add intelligence.html >> auto_run.log 2>&1
git commit -m "auto-update: 情报中心周更 %date%" >> auto_run.log 2>&1

echo [4/4] 推送到GitHub... >> auto_run.log
git push origin master:main --force >> auto_run.log 2>&1

echo ========================================== >> auto_run.log
echo [完成] 自动更新结束 >> auto_run.log
echo ========================================== >> auto_run.log
"@

# 将脚本写入临时批处理文件
$BatchPath = "$WorkDir\auto_run.bat"
$ActionScript | Out-File -FilePath $BatchPath -Encoding ASCII

$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchPath`"" -WorkingDirectory $WorkDir

# 任务设置
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RunOnlyIfNetworkAvailable

# 注册任务
Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $TaskDescription `
    -Trigger $Triggers `
    -Action $Action `
    -Settings $Settings `
    -RunLevel Highest `
    -Force

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "  定时任务创建成功！" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "任务详情:" -ForegroundColor White
Write-Host "  - 名称: $TaskName" -ForegroundColor Gray
Write-Host "  - 触发1: 每周一 10:00 AM" -ForegroundColor Gray
Write-Host "  - 触发2: 每周五 10:00 AM" -ForegroundColor Gray
Write-Host "  - 执行: 采集→生成→推送 完整流水线" -ForegroundColor Gray
Write-Host "  - 工作目录: $WorkDir" -ForegroundColor Gray
Write-Host ""
Write-Host "管理命令:" -ForegroundColor White
Write-Host "  查看任务: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor DarkGray
Write-Host "  立即运行: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor DarkGray
Write-Host "  删除任务: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor DarkGray
Write-Host "  查看日志: Get-Content '$WorkDir\auto_run.log'" -ForegroundColor DarkGray
Write-Host ""
Write-Host "下次执行时间:" -ForegroundColor Yellow

# 显示任务详情
Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo | Select-Object TaskName, NextRunTime, LastRunTime | Format-Table
