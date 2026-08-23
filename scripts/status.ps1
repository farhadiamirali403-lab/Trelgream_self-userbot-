# Show status of all processes + health check.
$ErrorActionPreference = 'Continue'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Pids = Join-Path $Root '.runtime\pids'

Write-Host "=== Process Status ==="
$names = @('backend','central_bot','worker_manager','scheduler')
foreach ($n in $names) {
    $pf = Join-Path $Pids "$n.pid"
    if (Test-Path $pf) {
        $pid = Get-Content $pf
        if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            Write-Host ("  {0,-15} RUNNING (PID {1})" -f $n, $pid) -ForegroundColor Green
        } else {
            Write-Host ("  {0,-15} STOPPED" -f $n) -ForegroundColor Red
        }
    } else {
        Write-Host ("  {0,-15} not started" -f $n) -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "=== Health ==="
try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    $h | ConvertTo-Json
} catch {
    Write-Host "Backend not reachable: $($_.Exception.Message)" -ForegroundColor Red
}
