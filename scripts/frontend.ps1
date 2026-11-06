param([switch]$Production)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (Test-Path "$projectRoot/tools/node/node.exe") { $env:Path = "$projectRoot/tools/node;" + $env:Path }
Push-Location "$projectRoot/frontend"
try {
    if ($Production) { & npm.cmd run start } else { & npm.cmd run dev }
} finally { Pop-Location }
