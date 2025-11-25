param(
    [string]$BuildDir = "$PSScriptRoot\build-win",
    [string]$InstallDir = "$PSScriptRoot\dist-win"
)

$projectRoot = Resolve-Path "$PSScriptRoot\..\.."

if (-not (Test-Path $BuildDir)) {
    New-Item -ItemType Directory -Force -Path $BuildDir | Out-Null
}
if (Test-Path $InstallDir) {
    Remove-Item -Recurse -Force $InstallDir
}

$cmakeArgs = @(
    "-S", (Join-Path $projectRoot "qt_app"),
    "-B", $BuildDir,
    "-G", "Ninja",
    "-DCMAKE_BUILD_TYPE=Release",
    "-DCMAKE_INSTALL_PREFIX=$InstallDir"
)

cmake @cmakeArgs
cmake --build $BuildDir
cmake --install $BuildDir

Write-Host "Qt binaries installed to $InstallDir"

