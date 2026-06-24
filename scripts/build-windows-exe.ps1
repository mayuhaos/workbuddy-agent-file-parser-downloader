param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "py"
}

if (-not $SkipInstall) {
    if ($Python -eq "py") {
        & $Python -3 -m pip install -e ".[gui,build]"
    } else {
        & $Python -m pip install -e ".[gui,build]"
    }
}

$PyInstallerArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name", "workbuddy-agent-file-parser-downloader-v1.0.0-windows-x64",
    "--icon", (Join-Path $RepoRoot "assets\workbuddy-agent-file-parser-downloader.ico"),
    "--collect-all", "customtkinter",
    "src\workbuddy_agent_file_parser_downloader\gui_entry.py"
)

if ($Python -eq "py") {
    & $Python -3 @PyInstallerArgs
} else {
    & $Python @PyInstallerArgs
}

Write-Host ""
Write-Host "Built: dist\workbuddy-agent-file-parser-downloader-v1.0.0-windows-x64.exe"
