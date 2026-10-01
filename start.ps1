$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$venvPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
    $pythonCandidates = @($bundledPython)
    $pythonCommand = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonCandidates += $pythonCommand.Source }
    $usablePython = $null
    foreach ($candidate in $pythonCandidates) {
        if ((Test-Path -LiteralPath $candidate) -and $candidate -notlike '*WindowsApps*') {
            $usablePython = $candidate
            break
        }
    }
    if ($usablePython) {
        & $usablePython -m venv .venv
    } elseif (Get-Command py.exe -ErrorAction SilentlyContinue) {
        & py.exe -3 -m venv .venv
    } else {
        throw 'Nainstalujte Python 3.12 alebo novsi a spustite start.cmd znova.'
    }
    if ($LASTEXITCODE -ne 0) { throw 'Nepodarilo sa vytvorit .venv. Nainstalujte Python 3.12+.' }
}
& $venvPython -c 'import fastapi, uvicorn, tzdata'
if ($LASTEXITCODE -ne 0) {
    & $venvPython -m pip install -r requirements.txt -c constraints.txt
    if ($LASTEXITCODE -ne 0) { throw 'Instalacia zlyhala. Pri prvom spusteni je potrebny internet.' }
}
Write-Host ''
Write-Host 'ENERGIA - LOKALNY DASHBOARD' -ForegroundColor Green
Write-Host 'Dashboard: http://127.0.0.1:8765'
$lanAddresses = Get-NetIPAddress -AddressFamily IPv4 -AddressState Preferred -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.InterfaceAlias -notlike '*Loopback*' } |
    Select-Object -ExpandProperty IPAddress -Unique
foreach ($address in $lanAddresses) { Write-Host "Mobil / iny PC: http://${address}:8765" }
Write-Host 'ESP32 kluc: data/device_key.txt (vytvori sa pri prvom starte)'
Write-Host 'Ukoncenie: Ctrl+C. Data zostanu v priecinku data.'
Write-Host ''
& $venvPython -m uvicorn backend.main:app --host 0.0.0.0 --port 8765 --workers 1
exit $LASTEXITCODE
