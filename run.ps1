# Central launcher menu.
$ErrorActionPreference = 'Continue'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '.')).Path

Write-Host ""
Write-Host "  Telegram Userbot SaaS — Launcher" -ForegroundColor Cyan
Write-Host "  ---------------------------------" -ForegroundColor Cyan
Write-Host "  1) Start"
Write-Host "  2) Stop"
Write-Host "  3) Restart"
Write-Host "  4) Status"
Write-Host "  0) Exit"
Write-Host ""

$choice = Read-Host "Select an option"
switch ($choice) {
    "1" { & (Join-Path $Root 'scripts\start.ps1') }
    "2" { & (Join-Path $Root 'scripts\stop.ps1') }
    "3" { & (Join-Path $Root 'scripts\restart.ps1') }
    "4" { & (Join-Path $Root 'scripts\status.ps1') }
    "0" { exit 0 }
    default { Write-Host "Invalid option" -ForegroundColor Red }
}
