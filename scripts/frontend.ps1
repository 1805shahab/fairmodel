param([switch]$Production, [ValidateRange(1,65535)][int]$Port = 3000)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (Test-Path "$projectRoot/tools/node/node.exe") { $env:Path = "$projectRoot/tools/node;" + $env:Path }
Push-Location "$projectRoot/frontend"
try {
    if ($Production) { & npm.cmd run start -- --port $Port } else { & npm.cmd run dev -- --port $Port }
} finally { Pop-Location }
