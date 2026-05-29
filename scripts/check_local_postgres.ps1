$ErrorActionPreference = "Stop"

$connection = Get-NetTCPConnection -LocalPort 5432 -ErrorAction SilentlyContinue |
    Where-Object { $_.State -eq "Listen" } |
    Select-Object -First 1

if (-not $connection) {
    Write-Host "PostgreSQL is not listening on port 5432."
    exit 1
}

$candidates = @(
    "E:\PostgreSQL\16-portable\pgsql\bin\psql.exe",
    "E:\PostgreSQL\16\bin\psql.exe",
    "D:\PostgreSQL\16\bin\psql.exe"
)

$psql = Get-Command psql -ErrorAction SilentlyContinue
$psqlPath = if ($psql) { $psql.Source } else { $candidates | Where-Object { Test-Path $_ } | Select-Object -First 1 }

if ($psqlPath) {
    Write-Host "psql found: $psqlPath"
} else {
    Write-Host "psql is not in PATH. The database may still be installed; init script can search common install paths."
}

Write-Host "PostgreSQL port 5432 is listening. Process ID: $($connection.OwningProcess)"
