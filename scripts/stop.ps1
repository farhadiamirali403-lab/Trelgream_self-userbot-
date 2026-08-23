# Stop all application processes.
$ErrorActionPreference = 'Continue'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Pids = Join-Path $Root '.runtime\pids'

if (Test-Path $Pids) {
    Get-ChildItem $Pids -Filter '*.pid' | ForEach-Object {
        $pid = Get-Content $_.FullName -ErrorAction SilentlyContinue
        if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            Stop-Process -Id $pid -Force
            Write-Host "Stopped $($_.BaseName) (PID $pid)" -ForegroundColor Yellow
        } else {
            Write-Host "$($_.BaseName): already stopped"
        }
        Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "No PID directory found."
}
Write-Host "Done."
