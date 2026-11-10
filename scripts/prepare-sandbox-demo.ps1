$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$mediaRoot = Join-Path $projectRoot 'backend\fixtures\paypal-sandbox-demo'
New-Item -ItemType Directory -Path $mediaRoot -Force | Out-Null
$recording = Join-Path $mediaRoot 'original-harbor-lamp-ad.wav'
$narration = @'
Meet Harbor Lantern, a fictional workshop that makes thoughtful lighting for quiet evenings. Our imaginary reading lamp pairs a warm shade with a simple wooden stand, bringing a comfortable glow to your favorite corner. Place it beside a stack of books, carry your sketchbook to the sofa, and give yourself a little time to make something new. The collection includes a desk light for creative afternoons and a compact bedside design for slower mornings. Each fictional product is described clearly, so you can compare the size, color, and finish before choosing a style. Browse the imagined collection online and discover how a small change can make your room feel welcoming. Harbor Lantern celebrates practical design, patient craftsmanship, and everyday creativity. Explore the product notes, consider the space you have, and find the light that fits your routine. This original synthetic advertisement was written for a software demonstration. The company and products are fictional, the recording uses an installed computer voice, and it does not imitate a real voice artist. No purchase, political endorsement, gambling offer, or real product claim is intended.
'@
if (-not (Test-Path -LiteralPath $recording)) {
    Add-Type -AssemblyName System.Speech
    $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
    try {
        $speaker.Rate = -1
        $speaker.SetOutputToWaveFile($recording)
        $speaker.Speak($narration)
        $speaker.SetOutputToNull()
    } finally { $speaker.Dispose() }
    Set-Content -LiteralPath (Join-Path $mediaRoot 'script.txt') -Value $narration -Encoding UTF8
}
Push-Location "$projectRoot/backend"
try {
    & './.venv/Scripts/python.exe' '../scripts/measure_sandbox_demo.py'
    if ($LASTEXITCODE -ne 0) { throw 'Demo audio measurement failed.' }
} finally { Pop-Location }
