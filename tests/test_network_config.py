import json
import shutil
import subprocess
import sys
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
pytestmark=pytest.mark.skipif(sys.platform!='win32',reason='Scripts exclusivos do Windows/Hamachi; núcleo e navegador são testados em Linux.')
SHELL = shutil.which("pwsh") or shutil.which("powershell")


def invoke(name, *args):
    return subprocess.run([SHELL, "-NoProfile", "-File", str(ROOT / "scripts" / name), *args], capture_output=True, text=True, encoding="utf-8")


def test_local_launch_is_loopback_only():
    result = invoke("start_local.ps1", "-CheckOnly")
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config["Address"] == "127.0.0.1"
    assert config["Port"] == 8501
    assert config["XsrfProtection"] is True


def test_firewall_dry_run_is_restricted_and_does_not_apply_rules():
    result = invoke("configure_firewall.ps1", "-HamachiAddress", "25.1.2.3", "-AllowedPeerAddresses", "25.1.2.4", "-CheckOnly")
    assert result.returncode == 0, result.stderr
    config = json.loads(result.stdout)
    assert config["LocalAddress"] == "25.1.2.3"
    assert config["RemoteAddress"] == ["25.1.2.4"]
    assert config["LocalPort"] == 8501
    assert config["InterfaceAlias"] == "Hamachi"
    assert config["Applied"] is False


def test_firewall_rejects_public_wildcard_and_path_values():
    for value in ("0.0.0.0", "127.0.0.1", "Any", "::1", "25.1.2.3;whoami"):
        result = invoke("configure_firewall.ps1", "-HamachiAddress", value, "-AllowedPeerAddresses", "25.1.2.4", "-CheckOnly")
        assert result.returncode != 0, value
        assert "IPv4 Hamachi" in result.stderr


def test_hamachi_launcher_rejects_unknown_interface_instead_of_binding_any():
    result = invoke("start_hamachi.ps1", "-HamachiAddress", "25.254.253.252", "-AllowedPeerAddresses", "25.254.253.251", "-CheckOnly")
    assert result.returncode != 0
    assert "Hamachi:" in result.stderr


def test_powershell_scripts_parse():
    script = "$errorsFound = @(); Get-ChildItem -LiteralPath 'scripts' -Filter '*.ps1' | ForEach-Object { $tokens=$null; $parseErrors=$null; [void][System.Management.Automation.Language.Parser]::ParseFile($_.FullName,[ref]$tokens,[ref]$parseErrors); $errorsFound += $parseErrors }; if ($errorsFound.Count) { $errorsFound | Out-String | Write-Error; exit 1 }"
    result = subprocess.run([SHELL, "-NoProfile", "-Command", script], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

def test_firewall_queries_use_compatible_parameter_sets():
    # Conferir contra o cmdlet real sem consultar ou alterar regras do Windows.
    script = r'''
$ErrorActionPreference='Stop'
$tokens=$null; $errorsFound=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Resolve-Path 'scripts/start_hamachi.ps1'),[ref]$tokens,[ref]$errorsFound)
$command=Get-Command Get-NetFirewallRule
$calls=$ast.FindAll({param($node) $node -is [System.Management.Automation.Language.CommandAst] -and $node.GetCommandName() -eq 'Get-NetFirewallRule'},$true)
foreach($call in $calls) {
    $names=@($call.CommandElements | Where-Object {$_ -is [System.Management.Automation.Language.CommandParameterAst]} | ForEach-Object {$_.ParameterName})
    $compatible=@($command.ParameterSets | Where-Object {
        $available=@($_.Parameters.Name)
        @($names | Where-Object {$_ -notin $available}).Count -eq 0
    })
    if(-not $compatible.Count) { throw ('Parametros incompativeis: '+($names -join ', ')) }
}
Write-Output 'Parameter sets valid'
'''
    result=subprocess.run(["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-Command",script],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode == 0,result.stderr
