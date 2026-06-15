# Passo 1 — avvia l'API in locale (senza Docker)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"

Set-Location $Backend

if (-not (Test-Path ".venv")) {
    Write-Host "Creo ambiente virtuale Python..."
    python -m venv .venv
}

Write-Host "Attivo venv e installo dipendenze (passo 1)..."
& ".\.venv\Scripts\Activate.ps1"
pip install -q -r requirements-step1.txt

Write-Host ""
Write-Host "WorkFlow Assistant — Passo 1"
Write-Host "  Health:  http://localhost:8000/health"
Write-Host "  Docs:    http://localhost:8000/docs"
Write-Host "  Ctrl+C per fermare"
Write-Host ""

uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
