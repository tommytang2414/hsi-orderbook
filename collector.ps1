$ErrorActionPreference = "Continue"
$projectDir = "C:\Users\user\hsi-orderbook"
$logDir = "$projectDir\logs"
$logFile = "$logDir\$(Get-Date -Format 'yyyyMMdd')_collector.log"

if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$env:PYTHONPATH = $projectDir
Set-Location $projectDir

$pythonExe = python
& $pythonExe -u "$projectDir\main.py" 2>&1 | Out-File -FilePath $logFile -Append -NoClobber
