$ErrorActionPreference = 'Stop'
$software = Join-Path $PSScriptRoot 'software'
$pilot = Join-Path $PSScriptRoot 'pilot'

Write-Host 'Checking software...'
Set-Location -LiteralPath $software
if (-not (Test-Path -LiteralPath (Join-Path $software 'node_modules'))) { npm install }
npm test
npm run build

Write-Host ''
Write-Host 'Checking pilot pipeline without a GPU...'
Set-Location -LiteralPath $pilot
python -m pytest -v

Write-Host ''
Write-Host 'MindMate verification completed successfully.'
