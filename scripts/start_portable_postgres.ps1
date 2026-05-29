param(
    [string]$PostgresHome = "E:\PostgreSQL\16-portable\pgsql",
    [string]$DataDir = "E:\PostgreSQL\16-portable\data",
    [string]$LogFile = "E:\PostgreSQL\16-portable\postgres.log",
    [int]$Port = 5432
)

$ErrorActionPreference = "Stop"

$pgCtl = Join-Path $PostgresHome "bin\pg_ctl.exe"
if (-not (Test-Path $pgCtl)) {
    throw "pg_ctl.exe was not found: $pgCtl"
}

$listening = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue |
    Where-Object { $_.State -eq "Listen" } |
    Select-Object -First 1

if ($listening) {
    Write-Host "PostgreSQL is already listening on port $Port. Process ID: $($listening.OwningProcess)"
    exit 0
}

& $pgCtl -D $DataDir -l $LogFile -o "-p $Port" start
Write-Host "PostgreSQL started on port $Port."
