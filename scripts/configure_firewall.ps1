[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory)][string]$HamachiAddress,
    [Parameter(Mandatory)][string[]]$AllowedPeerAddresses,
    [string]$HamachiInterfaceAlias = 'Hamachi',
    [switch]$CheckOnly
)
$ErrorActionPreference = 'Stop'
function Assert-HamachiIPv4([string]$Value) {
    $parsedAddress = $null
    if (-not [System.Net.IPAddress]::TryParse($Value, [ref]$parsedAddress) -or
        $parsedAddress.AddressFamily -ne [System.Net.Sockets.AddressFamily]::InterNetwork -or
        $parsedAddress.ToString() -ne $Value -or -not $Value.StartsWith('25.')) {
        throw 'Informe um IPv4 Hamachi no intervalo 25.0.0.0/8, sem curingas ou comandos.'
    }
}
Assert-HamachiIPv4 $HamachiAddress
if ($AllowedPeerAddresses.Count -eq 0) { throw 'Informe ao menos um cliente Hamachi autorizado.' }
foreach ($peerAddress in $AllowedPeerAddresses) { Assert-HamachiIPv4 $peerAddress }
if ($HamachiInterfaceAlias -notmatch '^[\p{L}\p{N} _().-]{1,80}$') { throw 'Nome de interface Hamachi inválido.' }
$ruleName = 'TCC Analyzer Hamachi 8501'
$configuration = [ordered]@{Name=$ruleName; LocalAddress=$HamachiAddress; RemoteAddress=@($AllowedPeerAddresses); LocalPort=8501; Protocol='TCP'; InterfaceAlias=$HamachiInterfaceAlias; Applied=$false}
if ($CheckOnly) { $configuration | ConvertTo-Json -Compress; exit 0 }
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = [Security.Principal.WindowsPrincipal]::new($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Abra PowerShell como administrador e execute novamente este configurador. Nenhuma regra foi alterada.'
}
$assigned = @(Get-NetIPAddress -AddressFamily IPv4 -IPAddress $HamachiAddress -ErrorAction SilentlyContinue | Where-Object InterfaceAlias -eq $HamachiInterfaceAlias)
if ($assigned.Count -ne 1) { throw 'O IPv4 informado não está atribuído à interface Hamachi indicada.' }
if ($PSCmdlet.ShouldProcess($ruleName, 'Criar ou atualizar regra restrita do aplicativo')) {
    $parameters = @{DisplayName=$ruleName; Direction='Inbound'; Action='Allow'; Enabled='True'; Profile='Any'; Protocol='TCP'; LocalPort=8501; LocalAddress=$HamachiAddress; RemoteAddress=$AllowedPeerAddresses; InterfaceAlias=$HamachiInterfaceAlias; EdgeTraversalPolicy='Block'}
    $existing = @(Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue)
    if ($existing.Count -gt 1) { throw 'Há regras duplicadas com o nome do aplicativo; revise-as manualmente antes de continuar.' }
    if ($existing.Count -eq 1) {
        Set-NetFirewallRule @parameters | Out-Null
    } else {
        New-NetFirewallRule @parameters | Out-Null
    }
    $configuration.Applied = $true
    $configuration | ConvertTo-Json -Compress
}
