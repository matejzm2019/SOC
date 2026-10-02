import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.skipif(not shutil.which('powershell.exe'), reason='Windows launcher')
def test_second_launch_reuses_dashboard_and_filters_non_lan_addresses():
    launcher = Path(__file__).resolve().parents[1] / 'start.ps1'
    command = r'''
function Invoke-RestMethod { param($Uri,$TimeoutSec) return @{app='energia';status='ok';version='test'} }
function Get-NetIPConfiguration {
    [CmdletBinding()] param()
    @(
        [pscustomobject]@{NetAdapter=@{Status='Up';HardwareInterface=$true};IPv4Address=@{IPAddress='10.138.124.103'}},
        [pscustomobject]@{NetAdapter=@{Status='Up';HardwareInterface=$false};IPv4Address=@{IPAddress='25.12.85.129'}},
        [pscustomobject]@{NetAdapter=@{Status='Up';HardwareInterface=$true};IPv4Address=@{IPAddress='169.254.83.107'}}
    )
}
function Start-Process { param($FilePath) Write-Output "OPEN:$FilePath" }
& 'LAUNCHER'
'''.replace('LAUNCHER', str(launcher).replace("'", "''"))
    result = subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-Command',command],
                            capture_output=True,text=True,timeout=15)
    assert result.returncode == 0, result.stderr
    assert 'Aplikacia uz bezi' in result.stdout
    assert 'OPEN:http://127.0.0.1:8765' in result.stdout
    assert '10.138.124.103' in result.stdout
    assert '25.12.85.129' not in result.stdout and '169.254.83.107' not in result.stdout
    assert 'uvicorn' not in result.stdout + result.stderr
