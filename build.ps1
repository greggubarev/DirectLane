$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Could not create the build environment.' }
}
$taskPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $taskPython -m pip install --disable-pip-version-check -r requirements-build.txt
if ($LASTEXITCODE -ne 0) { throw 'Could not install build dependencies.' }

& $taskPython -m PyInstaller --noconfirm --clean --windowed --onedir --name DirectLane `
    --add-data 'routes.ps1;.' --add-data 'catalog.json;.' `
    --distpath dist --workpath build\onedir manager.pyw
if ($LASTEXITCODE -ne 0) { throw 'Portable build failed.' }

& $taskPython -m PyInstaller --noconfirm --clean --windowed --onefile --name DirectLane `
    --add-data 'routes.ps1;.' --add-data 'catalog.json;.' `
    --distpath dist-single --workpath build\single manager.pyw
if ($LASTEXITCODE -ne 0) { throw 'Single-file build failed.' }

Write-Host 'Portable: dist\DirectLane\DirectLane.exe'
Write-Host 'Single file: dist-single\DirectLane.exe'
