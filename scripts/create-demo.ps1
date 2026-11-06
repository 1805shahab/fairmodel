$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location "$projectRoot/backend"
try {
    & './.venv/Scripts/python.exe' '../scripts/create_fixtures.py'
    if ($LASTEXITCODE -ne 0) { throw 'Fixture document generation failed' }
    # Windows' installed stock TTS voice. This is synthetic narration, not the fictional artist's voice.
    Add-Type -AssemblyName System.Speech
    $fixtureManifest = Get-Content -LiteralPath './fixtures/manifest.json' -Raw | ConvertFrom-Json
    $synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $synthesizer.Rate = -1
        $synthesizer.SetOutputToWaveFile("$projectRoot/backend/fixtures/sample-narration.wav")
        $synthesizer.Speak($fixtureManifest.transcript)
        $synthesizer.SetOutputToNull()
    } finally { $synthesizer.Dispose() }
    & './.venv/Scripts/python.exe' '../scripts/create_fixtures.py' '--finalize'
    if ($LASTEXITCODE -ne 0) { throw 'Fixture finalization failed' }
} finally { Pop-Location }
