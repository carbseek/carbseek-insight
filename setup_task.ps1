# CarbSeek Insight 每周自动更新 - 定时任务配置
# ============================================================
# 用法：以管理员身份运行 PowerShell，然后执行：
#   .\setup_task.ps1
# ============================================================

# 配置参数
$TaskName = "CarbSeekInsight_WeeklyUpdate"
$TaskDescription = "CarbSeek Insight 情报驾驶舱每周自动更新 - 每周一上午9:00执行"

# 脚本路径（请根据实际情况修改）
$WorkDir = "C:\Users\lipen\Documents\Kimi\Workspaces\carbseek\insight-update"
$BatchFile = "$WorkDir\auto_update.bat"

# 检查文件是否存在
if (-not (Test-Path $BatchFile)) {
    Write-Host "[错误] 找不到批处理文件: $BatchFile" -ForegroundColor Red
    Write-Host "请修改脚本中的 WorkDir 路径" -ForegroundColor Yellow
    exit 1
}

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  CarbSeek Insight 定时任务配置" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "任务名称: $TaskName" -ForegroundColor White
Write-Host "执行时间: 每周一 上午 9:00" -ForegroundColor White
Write-Host "执行脚本: $BatchFile" -ForegroundColor White
Write-Host ""

# 删除已有任务（如果存在）
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "[提示] 发现已有任务，先删除旧任务..." -ForegroundColor Yellow
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

# 创建触发器：每周一 9:00
$Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At "09:00"

# 创建操作：执行批处理文件
$Action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$BatchFile`"" -WorkingDirectory $WorkDir

# 创建任务设置
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# 注册任务（使用当前用户）
Register-ScheduledTask -TaskName $TaskName `
    -Description $TaskDescription `
    -Trigger $Trigger `
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
Write-Host "  - 触发: 每周一 9:00 AM" -ForegroundColor Gray
Write-Host "  - 操作: 执行 auto_update.bat" -ForegroundColor Gray
Write-Host "  - 工作目录: $WorkDir" -ForegroundColor Gray
Write-Host ""
Write-Host "管理命令:" -ForegroundColor White
Write-Host "  查看任务: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  运行任务: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Gray
Write-Host "  删除任务: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Gray
Write-Host ""
Write-Host "任务已启动，首次执行将在下周一 9:00" -ForegroundColor Yellow
Write-Host "如需立即测试，请运行: Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
Write-Host ""

# 显示任务列表
Get-ScheduledTask -TaskName $TaskName | Select-Object TaskName, State, NextRunTime | Format-Table
