param(
    [string]$PostgresUser = "postgres",
    [string]$PostgresPassword = "postgres",
    [string]$AppUser = "finance_copilot",
    [string]$AppPassword = "finance_copilot",
    [string]$DatabaseName = "finance_data_copilot",
    [string]$HostName = "localhost",
    [int]$Port = 5432
)

$ErrorActionPreference = "Stop"

function Find-Psql {
    $cmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    $candidates = @(
        "E:\PostgreSQL\16-portable\pgsql\bin\psql.exe",
        "E:\PostgreSQL\16\bin\psql.exe",
        "D:\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\18\bin\psql.exe",
        "C:\Program Files\PostgreSQL\17\bin\psql.exe",
        "C:\Program Files\PostgreSQL\16\bin\psql.exe",
        "C:\Program Files\PostgreSQL\15\bin\psql.exe",
        "C:\Program Files\PostgreSQL\14\bin\psql.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    throw "psql was not found. Please install PostgreSQL first."
}

$projectRoot = Split-Path -Parent $PSScriptRoot
$schemaPath = Join-Path $projectRoot "database\schema.sql"
$seedPath = Join-Path $projectRoot "database\seed.sql"
$psql = Find-Psql

Write-Host "Using psql: $psql"
Write-Host "Creating application user and database if needed..."
$env:PGPASSWORD = $PostgresPassword

$adminSql = @"
DO `$`$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$AppUser') THEN
        CREATE ROLE $AppUser LOGIN PASSWORD '$AppPassword';
    END IF;
END
`$`$;

SELECT 'CREATE DATABASE $DatabaseName OWNER $AppUser'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DatabaseName')\gexec
ALTER DATABASE $DatabaseName OWNER TO $AppUser;
"@

$adminSql | & $psql -h $HostName -p $Port -U $PostgresUser -d postgres -v ON_ERROR_STOP=1

Write-Host "Applying schema.sql..."
$env:PGPASSWORD = $AppPassword
& $psql -h $HostName -p $Port -U $AppUser -d $DatabaseName -v ON_ERROR_STOP=1 -f $schemaPath

Write-Host "Applying seed.sql..."
& $psql -h $HostName -p $Port -U $AppUser -d $DatabaseName -v ON_ERROR_STOP=1 -f $seedPath

Write-Host "Database is ready: $DatabaseName"
