# One-time setup: venv, dependencies, portable PostgreSQL + Redis, .env, DB.
$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root
$rt = Join-Path $Root '.runtime'
New-Item -ItemType Directory -Force -Path $rt | Out-Null

function Write-Step($m) { Write-Host "==> $m" -ForegroundColor Cyan }

# --- 1. Python ---
Write-Step "Checking Python"
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { Write-Error "Python یافت نشد. از python.org نسخه 3.12/3.13 را نصب کنید." }

# --- 2. venv ---
if (-not (Test-Path (Join-Path $Root '.venv'))) {
    Write-Step "Creating virtualenv"
    python -m venv .venv
}
$venvPython = Join-Path $Root '.venv\Scripts\python.exe'
Write-Step "Installing dependencies"
& $venvPython -m pip install --upgrade pip *> $null
& $venvPython -m pip install -r requirements.txt

# --- 3. Redis (portable) ---
$redisServer = Get-ChildItem $rt -Recurse -Filter 'redis-server.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $redisServer) {
    Write-Step "Downloading portable Redis"
    $zip = Join-Path $rt 'redis.zip'
    Invoke-WebRequest -Uri "https://github.com/tporadowski/redis/releases/download/v5.0.14.1/Redis-x64-5.0.14.1.zip" -OutFile $zip -UseBasicParsing
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($zip, (Join-Path $rt 'redis'))
}

# --- 4. PostgreSQL (portable) ---
$pgCtl = Join-Path $rt 'pgsql\bin\pg_ctl.exe'
if (-not (Test-Path $pgCtl)) {
    Write-Step "Downloading portable PostgreSQL 16"
    $jar = Join-Path $rt 'pg.jar'
    Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/io/zonky/test/postgres/embedded-postgres-binaries-windows-amd64/16.14.0/embedded-postgres-binaries-windows-amd64-16.14.0.jar" -OutFile $jar -UseBasicParsing
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [System.IO.Compression.ZipFile]::ExtractToDirectory($jar, (Join-Path $rt 'pg_extract'))
    tar.exe -xf (Join-Path $rt 'pg_extract\postgres-windows-x86_64.txz') -C (Join-Path $rt 'pgsql')
}

# --- 5. .env ---
if (-not (Test-Path (Join-Path $Root '.env'))) {
    Write-Step "Creating .env"
    Copy-Item (Join-Path $Root '.env.example') (Join-Path $Root '.env')
    $key = & $venvPython -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    $content = Get-Content (Join-Path $Root '.env') -Raw
    $content = $content -replace 'SESSION_ENCRYPTION_KEY=', "SESSION_ENCRYPTION_KEY=$key"
    Set-Content (Join-Path $Root '.env') $content -Encoding UTF8
}

# --- 6. Initialize & start PostgreSQL ---
$pgData = Join-Path $rt 'pgdata'
if (-not (Test-Path (Join-Path $pgData 'PG_VERSION'))) {
    Write-Step "Initializing PostgreSQL data directory"
    & (Join-Path $rt 'pgsql\bin\initdb.exe') -D $pgData -U postgres -A trust -E UTF8 --locale=C *> $null
}
& $pgCtl -D $pgData status *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Step "Starting PostgreSQL"
    & $pgCtl -D $pgData -l (Join-Path $rt 'pglog.txt') -o "-p 5432" start *> $null
    Start-Sleep -Seconds 3
}

# --- 7. Start Redis ---
$redisCli = Get-ChildItem $rt -Recurse -Filter 'redis-cli.exe' | Select-Object -First 1 -ExpandProperty FullName
$ping = & $redisCli ping 2>$null
if ($ping -ne 'PONG') {
    Write-Step "Starting Redis"
    $rs = Get-ChildItem $rt -Recurse -Filter 'redis-server.exe' | Select-Object -First 1 -ExpandProperty FullName
    Start-Process -FilePath $rs -ArgumentList "--port","6379" -WorkingDirectory (Split-Path $rs) -WindowStyle Hidden
    Start-Sleep -Seconds 2
}

# --- 8. Database + migrations + seed ---
Write-Step "Creating database (if missing)"
& $venvPython (Join-Path $Root 'scripts\_setup_db.py')
Write-Step "Running migrations"
& $venvPython -m alembic upgrade head
Write-Step "Seeding"
& $venvPython (Join-Path $Root 'scripts\seed.py')

Write-Host ""
Write-Host "Setup complete." -ForegroundColor Green
Write-Host "Next: fill TELEGRAM_API_ID / TELEGRAM_API_HASH / CENTRAL_BOT_TOKEN / OWNER_TELEGRAM_ID in .env" -ForegroundColor Yellow
Write-Host "Then run: .\scripts\start.ps1" -ForegroundColor Cyan
