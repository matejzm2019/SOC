$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$dashboardUrl = 'http://127.0.0.1:8765'

function Get-EnergiaServer {
    try {
        $health = Invoke-RestMethod -Uri "$dashboardUrl/api/health" -TimeoutSec 2
        if ($health.app -eq 'energia') { return $health }
        # Earlier releases did not include an application identifier.
        if ($health.mode -in @('demo', 'monitor') -and $health.version) {
            $schema = Invoke-RestMethod -Uri "$dashboardUrl/openapi.json" -TimeoutSec 2
            if ($schema.info.title -eq 'Energia') { return $health }
        }
    } catch { }
    return $null
}

Write-Host ''
Write-Host 'ENERGIA - LOKALNY DASHBOARD' -ForegroundColor Cyan
Write-Host "Dashboard: $dashboardUrl"
try {
    $lanAddresses = Get-NetIPConfiguration -ErrorAction Stop |
        Where-Object { $_.NetAdapter.Status -eq 'Up' -and $_.NetAdapter.HardwareInterface } |
        ForEach-Object { $_.IPv4Address.IPAddress } |
        Where-Object { $_ -and $_ -notlike '127.*' -and $_ -notlike '169.254.*' } |
        Select-Object -Unique
    foreach ($address in $lanAddresses) { Write-Host "Mobil / iny PC: http://${address}:8765" }
} catch {
    Write-Host 'LAN adresu sa nepodarilo zistit. PC a mobil pripojte k rovnakej Wi-Fi.'
}

$existingServer = Get-EnergiaServer
if ($existingServer) {
    Write-Host "Aplikacia uz bezi (v$($existingServer.version)). Otvaram dashboard; druhy server nespustam." -ForegroundColor Cyan
    Start-Process $dashboardUrl
    exit 0
}

$portCheck = New-Object System.Net.Sockets.TcpClient
try {
    $connection = $portCheck.ConnectAsync('127.0.0.1', 8765)
    $portOccupied = $connection.Wait(500) -and $portCheck.Connected
} catch { $portOccupied = $false }
finally { $portCheck.Dispose() }
if ($portOccupied) {
    # A second launch may reach this check while the first server is starting.
    for ($attempt = 0; $attempt -lt 3; $attempt++) {
        Start-Sleep -Milliseconds 500
        $existingServer = Get-EnergiaServer
        if ($existingServer) {
            Write-Host 'Aplikacia uz bezi. Otvaram dashboard.'
            Start-Process $dashboardUrl
            exit 0
        }
    }
    throw 'Port 8765 pouziva ina aplikacia alebo neodpovedajuci server. Uvolnite tento port a spustite start.cmd znova. Ziadny cudzi proces nebol ukonceny.'
}

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
& $venvPython -c 'import fastapi, uvicorn, tzdata, httpx'
if ($LASTEXITCODE -ne 0) {
    & $venvPython -m pip install -r requirements.txt -c constraints.txt
    if ($LASTEXITCODE -ne 0) { throw 'Instalacia zlyhala. Pri prvom spusteni je potrebny internet.' }
}
Write-Host 'ESP32 kluc: data/device_key.txt (vytvori sa pri prvom starte)'
Write-Host 'Ukoncenie: Ctrl+C. Data zostanu v priecinku data.'
Write-Host ''
& $venvPython -m uvicorn backend.main:app --host 0.0.0.0 --port 8765 --workers 1
exit $LASTEXITCODE
