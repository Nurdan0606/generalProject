param([ValidateSet('start', 'stop', 'status')][string]$Action = 'start')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$control = Join-Path $projectRoot '.local\pgsql\bin\pg_ctl.exe'
$data = Join-Path $projectRoot '.local\pgdata'
$serverLog = Join-Path $projectRoot '.local\postgres.log'
if (-not (Test-Path -LiteralPath $control) -or -not (Test-Path -LiteralPath (Join-Path $data 'PG_VERSION'))) {
    throw 'Project-local PostgreSQL is not installed. Follow the PostgreSQL setup section in README.md.'
}
$arguments = @('-D', ('"' + $data + '"'))
if ($Action -eq 'start') { $arguments += @('-l', ('"' + $serverLog + '"'), '-w', 'start') }
elseif ($Action -eq 'stop') { $arguments += @('-m', 'fast', '-w', 'stop') }
else { $arguments += 'status' }
$controlLog = Join-Path $projectRoot '.local\postgres-control.log'
$errorLog = Join-Path $projectRoot '.local\postgres-control-error.log'
$process = Start-Process -FilePath $control -ArgumentList $arguments -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $controlLog -RedirectStandardError $errorLog
# Cache the handle so Windows PowerShell retains the exit code after exit.
$processHandle = $process.Handle
# Wait only for pg_ctl, not the PostgreSQL server it launches.
$process.WaitForExit()
Get-Content -LiteralPath $controlLog
if ($process.ExitCode -ne 0) {
    Get-Content -LiteralPath $errorLog
    throw "PostgreSQL $Action returned exit code $($process.ExitCode). See .local/postgres.log."
}
