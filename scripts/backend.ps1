param([switch]$NoReload, [switch]$PayPalSandbox, [switch]$MockPayments, [switch]$EnableSandboxDrafts, [switch]$EnableSandboxSending)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if ($MockPayments -and ($PayPalSandbox -or $EnableSandboxDrafts -or $EnableSandboxSending)) { throw 'Mock payments cannot enable Sandbox actions.' }
if (-not $MockPayments) {
    $env:PAYMENT_PROVIDER = 'paypal_sandbox'
    $env:PAYPAL_ALLOW_DRAFTS = if ($EnableSandboxDrafts) { 'true' } else { 'false' }
    $env:PAYPAL_ALLOW_SENDING = if ($EnableSandboxSending) { 'true' } else { 'false' }
    Write-Host 'FairModel: PayPal Sandbox selected. No automatic invoice or payment actions.'
} else {
    $env:PAYMENT_PROVIDER = 'mock'
    $env:PAYPAL_ALLOW_DRAFTS = 'false'
    $env:PAYPAL_ALLOW_SENDING = 'false'
    Write-Host 'FairModel: local simulated payments explicitly selected.'
}
$ffprobeTool = Get-ChildItem -LiteralPath "$projectRoot/tools/ffmpeg-dist" -Filter 'ffprobe.exe' -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
if ($ffprobeTool) { $env:Path = $ffprobeTool.Directory.FullName + ';' + $env:Path }
Push-Location "$projectRoot/backend"
try {
    $uvicornArgs = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000')
    if (-not $NoReload) { $uvicornArgs += '--reload' }
    & './.venv/Scripts/python.exe' @uvicornArgs
} finally { Pop-Location }
