[CmdletBinding()]
param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$configuration = [ordered]@{Address='127.0.0.1'; Port=8501; XsrfProtection=$true}
if ($CheckOnly) { $configuration | ConvertTo-Json -Compress; exit 0 }
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Instale o ambiente .venv conforme o README antes de iniciar.' }
Push-Location -LiteralPath $projectRoot
try {
    & $pythonPath -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.enableXsrfProtection true --server.enableCORS true --server.enableStaticServing false --browser.gatherUsageStats false
    exit $LASTEXITCODE
} finally { Pop-Location }
