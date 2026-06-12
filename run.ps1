$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$OutDir = Join-Path $ProjectRoot "outputs"

Set-Location $ProjectRoot

if (!(Test-Path $VenvPython)) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Installing/updating dependencies..."
& $VenvPython -m pip install -e .

$argsList = @(
    "-m", "workbuddy_agent_file_parser_downloader", "sync",
    "--out-dir", $OutDir,
    "--concurrency", "1",
    "--delay-min", "1",
    "--delay-max", "2"
)

if ($env:WORKBUDDY_XLSX_TEMPLATE -and (Test-Path $env:WORKBUDDY_XLSX_TEMPLATE)) {
    $argsList += @("--xlsx-template", $env:WORKBUDDY_XLSX_TEMPLATE)
}

Write-Host "Starting WorkBuddy sync..."
& $VenvPython @argsList

Write-Host ""
Write-Host "Done. Outputs:"
Write-Host $OutDir

