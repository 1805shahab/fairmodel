$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location "$projectRoot/backend"
try {
    if (-not (Test-Path -LiteralPath './fixtures/manifest.json')) { throw 'Generate the base fixtures using scripts/create-demo.ps1 first.' }
    & './.venv/Scripts/python.exe' '../scripts/scenario_fixtures.py'
    if ($LASTEXITCODE -ne 0) { throw 'Scenario preparation failed.' }
    $scenarioSpec = Get-Content -LiteralPath './fixtures/scenarios.json' -Raw | ConvertFrom-Json
    $missingVoiceCases = @($scenarioSpec.cases | Where-Object { $_.type -eq 'stock_tts' -and -not (Test-Path -LiteralPath (Join-Path "$projectRoot/backend/fixtures" $_.file)) })
    if ($missingVoiceCases.Count -gt 0) {
        Add-Type -AssemblyName System.Speech
        $synthesizer = New-Object System.Speech.Synthesis.SpeechSynthesizer
        try {
            $synthesizer.Rate = -1
            foreach ($scenarioCase in $missingVoiceCases) {
                $scenarioPath = Join-Path "$projectRoot/backend/fixtures" $scenarioCase.file
                $synthesizer.SetOutputToWaveFile($scenarioPath)
                $synthesizer.Speak($scenarioCase.transcript)
                $synthesizer.SetOutputToNull()
            }
        } finally { $synthesizer.Dispose() }
    }
    & './.venv/Scripts/python.exe' '../scripts/scenario_fixtures.py' '--finalize'
    if ($LASTEXITCODE -ne 0) { throw 'Scenario finalization failed.' }
} finally { Pop-Location }
