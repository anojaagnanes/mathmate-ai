$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Set-Location $projectRoot
if (-not (Test-Path 'backend/.venv/Scripts/python.exe')) {
    python -m venv --without-pip backend/.venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
python -m pip --python backend/.venv/Scripts/python.exe install -r backend/requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
if (-not (Test-Path 'backend/.env')) {
    $taskSecret = python -c "import secrets; print(secrets.token_urlsafe(48))"
    @("DATABASE_URL=sqlite:///./mathmate.db", "JWT_SECRET=$taskSecret", "FRONTEND_ORIGIN=http://localhost:3000", "AI_PROVIDER=mock") | Set-Content backend/.env
}
Push-Location backend
try {
    .venv/Scripts/python -m alembic upgrade head
    if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
    .venv/Scripts/python -m app.seed
    if ($LASTEXITCODE -ne 0) { throw 'Database seed failed.' }
} finally { Pop-Location }
Push-Location frontend
try { npm ci; if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' } } finally { Pop-Location }
Write-Host 'Setup complete. Follow README.md to start the backend and frontend.'
