[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$HamachiAddress,
    [Parameter(Mandatory)][string[]]$AllowedPeerAddresses,
    [string]$HamachiInterfaceAlias = 'Hamachi',
    [switch]$AllowAnyBind,
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
# Reuse the configurator's validation-only mode; this never writes a firewall rule.
$policyJson = & (Join-Path $PSScriptRoot 'configure_firewall.ps1') -HamachiAddress $HamachiAddress -AllowedPeerAddresses $AllowedPeerAddresses -HamachiInterfaceAlias $HamachiInterfaceAlias -CheckOnly
$policy = $policyJson | ConvertFrom-Json
$assigned = @(Get-NetIPAddress -AddressFamily IPv4 -IPAddress $HamachiAddress -ErrorAction SilentlyContinue | Where-Object InterfaceAlias -eq $HamachiInterfaceAlias)
if ($assigned.Count -ne 1) { throw 'Hamachi: o endereço informado não pertence à interface indicada. O servidor não foi iniciado.' }
$ruleName = 'TCC Analyzer Hamachi 8501'
$rules = @(Get-NetFirewallRule -DisplayName $ruleName -Enabled True -Direction Inbound -Action Allow -ErrorAction SilentlyContinue)
if ($rules.Count -ne 1) { throw 'Hamachi: configure primeiro a regra restrita com scripts/configure_firewall.ps1 como administrador.' }
$port = $rules[0] | Get-NetFirewallPortFilter
$address = $rules[0] | Get-NetFirewallAddressFilter
$interface = $rules[0] | Get-NetFirewallInterfaceFilter
if ($port.Protocol -notin @('TCP','6') -or "$($port.LocalPort)" -ne '8501' -or
    @($address.LocalAddress).Count -ne 1 -or $address.LocalAddress -ne $HamachiAddress -or
    @($interface.InterfaceAlias).Count -ne 1 -or $interface.InterfaceAlias -ne $HamachiInterfaceAlias -or
    @(Compare-Object @($address.RemoteAddress | Sort-Object -Unique) @($AllowedPeerAddresses | Sort-Object -Unique)).Count -ne 0) {
    throw 'Hamachi: a regra deve limitar TCP/8501 ao IP/interface Hamachi e aos clientes autorizados exatos.'
}
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Instale o ambiente .venv conforme o README antes de iniciar.' }
$basePythonPath = & $pythonPath -c 'import sys; print(sys._base_executable)'
if (@(Get-NetFirewallProfile | Where-Object Enabled -ne $true).Count -gt 0) { throw 'Hamachi: habilite os perfis do Windows Firewall antes de iniciar o servidor.' }
# A second broad allow rule can override the intended restriction. Refuse it.
foreach ($otherRule in @(Get-NetFirewallRule -Enabled True -Direction Inbound -Action Allow | Where-Object DisplayName -ne $ruleName)) {
    $application = $otherRule | Get-NetFirewallApplicationFilter
    if ($application.Program -ne 'Any' -and $application.Program -ne $pythonPath -and $application.Program -ne $basePythonPath) { continue }
    $otherPort = $otherRule | Get-NetFirewallPortFilter
    if ($otherPort.Protocol -notin @('TCP','6','Any','256')) { continue }
    $coversPort = $false
    foreach ($portEntry in @($otherPort.LocalPort)) {
        if ($portEntry -in @('Any','8501')) { $coversPort = $true }
        elseif ($portEntry -match '^(\d+)-(\d+)$' -and 8501 -ge [int]$Matches[1] -and 8501 -le [int]$Matches[2]) { $coversPort = $true }
    }
    if (-not $coversPort) { continue }
    $otherAddress = $otherRule | Get-NetFirewallAddressFilter
    $otherInterface = $otherRule | Get-NetFirewallInterfaceFilter
    $localMatches = @($otherAddress.LocalAddress).Count -eq 1 -and $otherAddress.LocalAddress -eq $HamachiAddress
    $interfaceMatches = @($otherInterface.InterfaceAlias).Count -eq 1 -and $otherInterface.InterfaceAlias -eq $HamachiInterfaceAlias
    $peersMatch = @(Compare-Object @($otherAddress.RemoteAddress | Sort-Object -Unique) @($AllowedPeerAddresses | Sort-Object -Unique)).Count -eq 0
    if (-not ($localMatches -and $interfaceMatches -and $peersMatch)) {
        throw 'Hamachi: uma regra de entrada adicional permite acesso mais amplo à porta/processo. Revise as regras do Windows Firewall; nenhuma foi removida automaticamente.'
    }
}
$bindAddress = if ($AllowAnyBind) { '0.0.0.0' } else { $HamachiAddress }
if ($CheckOnly) { [ordered]@{Address=$bindAddress; Port=8501; FirewallVerified=$true; XsrfProtection=$true} | ConvertTo-Json -Compress; exit 0 }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Instale o ambiente .venv conforme o README antes de iniciar.' }
Push-Location -LiteralPath $projectRoot
try {
    & $pythonPath -m streamlit run app.py --server.address $bindAddress --server.port 8501 --server.enableXsrfProtection true --server.enableCORS true --server.enableStaticServing false --browser.gatherUsageStats false
    exit $LASTEXITCODE
} finally { Pop-Location }
