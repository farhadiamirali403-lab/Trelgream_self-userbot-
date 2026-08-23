# Start all platform processes (backend, central bot, worker manager, scheduler).
$ErrorActionPreference = 'Continue'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root

$Python = Join-Path $Root '.venv\Scripts\python.exe'
$PgBin = Join-Path $Root '.runtime\pgsql\bin'
$PgData = Join-Path $Root '.runtime\pgdata'
$Pids = Join-Path $Root '.runtime\pids'
$Logs = Join-Path $Root '.runtime\logs'
New-Item -ItemType Directory -Force -Path $Pids, $Logs | Out-Null

function Write-Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }

if (-not (Test-Path $Python)) { Write-Error "venv یافت نشد. ابتدا setup را اجرا کنید."; exit 1 }
if (-not (Test-Path (Join-Path $Root '.env'))) { Write-Error ".env یافت نشد. از .env.example کپی کنید."; exit 1 }

# --- PostgreSQL ---
$pgCtl = Join-Path $PgBin 'pg_ctl.exe'
if (Test-Path $pgCtl) {
    & $pgCtl -D $PgData status *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Step "Starting PostgreSQL..."
        # Detached so the server survives this script's console.
        Start-Process -FilePath $pgCtl -ArgumentList "-D",$PgData,"-l",(Join-Path $Logs 'postgres.log'),"-o","-p 5432","start" -WindowStyle Hidden
        Start-Sleep -Seconds 3
    } else {
        Write-Step "PostgreSQL already running"
    }
} else {
    Write-Host "PostgreSQL binaries not found (skipping)" -ForegroundColor Yellow
}

# --- Redis ---
$redisServer = Get-ChildItem (Join-Path $Root '.runtime\redis') -Recurse -Filter 'redis-server.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
$redisCli = Get-ChildItem (Join-Path $Root '.runtime\redis') -Recurse -Filter 'redis-cli.exe' -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty FullName
if ($redisServer) {
    $ping = "NORESPONSE"
    if ($redisCli) { $ping = & $redisCli ping 2>$null }
    if ($ping -ne 'PONG') {
        Write-Step "Starting Redis..."
        Start-Process -FilePath $redisServer -ArgumentList "--port","6379" -WorkingDirectory (Split-Path $redisServer) -WindowStyle Hidden
        Start-Sleep -Seconds 2
    } else {
        Write-Step "Redis already running"
    }
}

# --- Xray proxy (اختیاری — اگر تلگرام در شبکه مسدود است) ---
$xrayExe = Join-Path $Root '.runtime\xray\xray.exe'
if (Test-Path $xrayExe) {
    $xrayRunning = Get-Process -Name "xray" -ErrorAction SilentlyContinue
    if (-not $xrayRunning) {
        Write-Step "Starting Xray proxy (127.0.0.1:10808)..."
        Start-Process -FilePath $xrayExe -ArgumentList "run","-c",(Join-Path $Root '.runtime\xray\config.json') -WorkingDirectory (Join-Path $Root '.runtime\xray') -WindowStyle Hidden
        Start-Sleep -Seconds 3
    } else {
        Write-Step "Xray proxy already running"
    }
}

# --- Migrations + seed ---
Write-Step "Running migrations..."
& $Python -m alembic upgrade head *> $null
Write-Step "Seeding data..."
& $Python scripts\seed.py *> $null

# --- Application processes ---
function Start-AppProcess([string]$name, [string[]]$AppArgs) {
    $out = Join-Path $Logs "$name.out.log"
    $err = Join-Path $Logs "$name.err.log"
    $proc = Start-Process -FilePath $Python -ArgumentList $AppArgs -WorkingDirectory $Root -PassThru -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
    $proc.Id | Set-Content (Join-Path $Pids "$name.pid")
    Write-Host "  Started $name (PID $($proc.Id))" -ForegroundColor Green
}

Write-Step "Starting application processes..."
Start-AppProcess "backend" @("-m","app.api")
Start-AppProcess "central_bot" @("-m","app.bot")
Start-AppProcess "worker_manager" @("-m","app.workers")
Start-AppProcess "scheduler" @("-m","app.scheduler")

Write-Host ""
Write-Host "All processes started." -ForegroundColor Green
Write-Host "Backend:  http://127.0.0.1:8000/docs" -ForegroundColor Cyan
