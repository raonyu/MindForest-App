param([switch]$PrepareOnly)
$ErrorActionPreference = 'Stop'
$taskRoot = $PSScriptRoot
$python = Join-Path $taskRoot '.venv\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Create .venv and install backend/B/backend/requirement.txt first.' }
$runtime = Join-Path $taskRoot '.local'
New-Item -ItemType Directory -Path $runtime -Force | Out-Null
$dbFile = Join-Path $runtime 'mindforest.db'
$previousDatabase = $env:DATABASE_URL
$previousEncoding = $env:PYTHONIOENCODING
$env:PYTHONIOENCODING = 'utf-8'
$env:DATABASE_URL = 'sqlite:///' + ($dbFile -replace '\\','/')
try {
    if (Test-Path -LiteralPath $dbFile) {
        & $python -c "import sqlite3,sys; a=sqlite3.connect(sys.argv[1]); b=sqlite3.connect(sys.argv[2]); a.backup(b); b.close(); a.close()" $dbFile ($dbFile + '.backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
        if ($LASTEXITCODE -ne 0) { throw 'Database backup failed.' }
    }
    Push-Location (Join-Path $taskRoot 'backend\B\backend')
    try {
        & $python migrate_report_fields.py
        if ($LASTEXITCODE -ne 0) { throw 'Database preparation failed.' }
        & $python seed_animals.py
        if ($LASTEXITCODE -ne 0) { throw 'Animal initialization failed.' }
        & $python data_seed.py
        if ($LASTEXITCODE -ne 0) { throw 'Survey initialization failed.' }
        & $python seed_routines.py
        if ($LASTEXITCODE -ne 0) { throw 'Routine initialization failed.' }
    } finally { Pop-Location }
    if ($PrepareOnly) { Write-Output 'Local database ready.'; return }
    Write-Output 'Backend: http://127.0.0.1:8000/docs'
    Write-Output 'In a second terminal: cd frontend; npm.cmd run web'
    & $python -m uvicorn main:app --app-dir (Join-Path $taskRoot 'backend\B\backend') --host 127.0.0.1 --port 8000
} finally { $env:DATABASE_URL = $previousDatabase; $env:PYTHONIOENCODING = $previousEncoding }
