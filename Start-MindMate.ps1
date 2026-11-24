$ErrorActionPreference = 'Stop'
$project = Join-Path $PSScriptRoot 'software'
Set-Location -LiteralPath $project

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    throw 'Node.js 20 or newer is required. Install Node.js, then run this file again.'
}

if (-not (Test-Path -LiteralPath (Join-Path $project 'node_modules'))) {
    Write-Host 'Installing MindMate software dependencies...'
    npm install
}

Write-Host ''
Write-Host 'Building MindMate...'
npm run build
if ($LASTEXITCODE -ne 0) { throw 'MindMate could not be built.' }

Write-Host ''
Write-Host 'Starting MindMate on one reliable server...'
Write-Host 'Open http://localhost:8080/ in your browser.'
Write-Host 'Press Ctrl+C in this window to stop the software.'
npm start
