# Restart all application processes.
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
& (Join-Path $Root 'scripts\stop.ps1')
Start-Sleep -Seconds 2
& (Join-Path $Root 'scripts\start.ps1')
