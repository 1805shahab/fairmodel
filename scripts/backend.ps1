param([switch]$NoReload)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$ffprobeTool = Get-ChildItem -LiteralPath "$projectRoot/tools/ffmpeg-dist" -Filter 'ffprobe.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($ffprobeTool) { $env:Path = $ffprobeTool.Directory.FullName + ';' + $env:Path }
Push-Location "$projectRoot/backend"
try {
    $uvicornArgs = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000')
    if (-not $NoReload) { $uvicornArgs += '--reload' }
    & './.venv/Scripts/python.exe' @uvicornArgs
} finally { Pop-Location }
