param(
    [string]$PostgresHome = "E:\PostgreSQL\16-portable\pgsql",
    [string]$DataDir = "E:\PostgreSQL\16-portable\data"
)

$ErrorActionPreference = "Stop"

$pgCtl = Join-Path $PostgresHome "bin\pg_ctl.exe"
if (-not (Test-Path $pgCtl)) {
    throw "pg_ctl.exe was not found: $pgCtl"
}

& $pgCtl -D $DataDir stop
Write-Host "PostgreSQL stopped."
