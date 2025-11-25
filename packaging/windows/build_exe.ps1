param(
    [string]$Version = "1.0.0",
    [string]$OutputDir = "$PSScriptRoot/dist"
)

$projectRoot = Resolve-Path "$PSScriptRoot/../.."
$specName = "IELTSForm"
$mainScript = Join-Path $projectRoot "ielts_form_gtk.py"
$iconPath = Join-Path $projectRoot "ielts_icon.png"

if (-not (Test-Path $mainScript)) {
    Write-Error "Cannot find $mainScript. Run this script from the repository."
    exit 1
}

if (-not (Get-Command pyinstaller -ErrorAction SilentlyContinue)) {
    Write-Error "PyInstaller not found. Run: pip install pyinstaller"
    exit 1
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$env:PYINSTALLER_CONFIG_DIR = Join-Path $OutputDir "config"
New-Item -ItemType Directory -Force -Path $env:PYINSTALLER_CONFIG_DIR | Out-Null

$dataArgs = @(
    "--add-data", "$($iconPath);."
)

$pyArgs = @(
    "--name", $specName,
    "--noconfirm",
    "--noconsole",
    "--clean",
    "--onefile"
) + $dataArgs + @($mainScript)

pyinstaller @pyArgs

$builtExe = Join-Path (Join-Path $projectRoot "dist") "$specName.exe"
if (Test-Path $builtExe) {
    Copy-Item $builtExe (Join-Path $OutputDir "IELTSForm-$Version.exe") -Force
    Write-Host "Created $(Join-Path $OutputDir "IELTSForm-$Version.exe")"
} else {
    Write-Warning "PyInstaller did not produce $builtExe. Check the build log."
}

