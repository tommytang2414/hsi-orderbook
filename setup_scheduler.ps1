# Setup Windows Task Scheduler for HSI OrderBook Collector
# HK Market Hours: 9:30am-12pm / 1pm-4pm HKT

$projectDir = "C:\Users\user\hsi-orderbook"
$pythonExe = "python"
$scriptPath = "$projectDir\main.py"

# Task to start at HK market open (9:30am HKT)
$taskName = "HSI_OrderBook_Collector"

# Remove existing task if present
schtasks /Delete /TN $taskName /F 2>$null

# Create task to run daily at 9:30am Hong Kong Time (UTC+8)
# Windows Task Scheduler uses local time, HK is UTC+8 which matches Windows timezone setting
schtasks /Create `
    /TN $taskName `
    /TR "$pythonExe `"$scriptPath`"" `
    /SC DAILY `
    /ST 09:30 `
    /MO 1 `
    /F

Write-Host "Task '$taskName' created. Will run daily at 9:30am HKT."
Write-Host "The collector runs for 10 hours, covering both morning (9:30-12) and afternoon (1-4pm) sessions."
Write-Host ""
Write-Host "To check task status:"
Write-Host "  schtasks /Query /TN '$taskName'"
Write-Host ""
Write-Host "To run manually now:"
Write-Host "  schtasks /Run /TN '$taskName'"
Write-Host ""
Write-Host "To delete:"
Write-Host "  schtasks /Delete /TN '$taskName' /F"
