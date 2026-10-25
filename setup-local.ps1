param([switch]$Verify, [switch]$WithModelDeps)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$python = Join-Path $taskRoot '.venv\Scripts\python.exe'
$previousEncoding = $env:PYTHONIOENCODING
$env:PYTHONIOENCODING = 'utf-8'
try {
    Push-Location $taskRoot
    try {
        if (!(Test-Path -LiteralPath $python)) {
            & py -3 -m venv .venv
            if ($LASTEXITCODE -ne 0) { throw 'Python 3 and the Windows Python launcher are required.' }
        }
        & $python -m pip install -r backend/B/backend/requirement.txt
        if ($LASTEXITCODE -ne 0) { throw 'Backend dependency installation failed.' }
        if ($WithModelDeps) {
            & $python -m pip install -r backend/emotion_model/requirements.txt
            if ($LASTEXITCODE -ne 0) { throw 'Optional model dependencies failed to install.' }
        }
        Push-Location (Join-Path $taskRoot 'frontend')
        try {
            & npm.cmd ci
            if ($LASTEXITCODE -ne 0) { throw 'Install Node.js 20+ and retry npm ci.' }
            if ($Verify) {
                & npm.cmd run typecheck
                if ($LASTEXITCODE -ne 0) { throw 'Typecheck failed.' }
                & npm.cmd run lint -- --quiet
                if ($LASTEXITCODE -ne 0) { throw 'Lint failed.' }
            }
        } finally { Pop-Location }
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $taskRoot 'start-local.ps1') -PrepareOnly
        if ($LASTEXITCODE -ne 0) { throw 'Local database preparation failed.' }
        if ($Verify) {
            & $python -m unittest discover -s backend/B/backend/tests -v
            if ($LASTEXITCODE -ne 0) { throw 'Integration tests failed.' }
        }
        Write-Output 'Setup ready. Run start-local.ps1 for the API, then npm.cmd run web in frontend.'
        Write-Output 'Real inference additionally requires the trained model files. GPT/BWS requires your own API key.'
    } finally { Pop-Location }
} finally { $env:PYTHONIOENCODING = $previousEncoding }
