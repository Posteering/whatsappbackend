# ============================================
# VIOLET WhatsApp Bot - Startup Script
# Run this from the project root folder:
#   .\start.ps1
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VIOLET WhatsApp Bot - Starting Up..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Start Celery Worker in a new terminal window
Write-Host "[1/3] Starting Celery Worker..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'c:\Users\USER\whatsapp bot'; Write-Host 'CELERY WORKER - DO NOT CLOSE' -ForegroundColor Green; venv\Scripts\python.exe -m celery -A app.core.celery_app worker --loglevel=info --pool=solo"

Start-Sleep -Seconds 2

# 2. Start FastAPI Server in a new terminal window
Write-Host "[2/3] Starting FastAPI Server..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'c:\Users\USER\whatsapp bot'; Write-Host 'FASTAPI SERVER - DO NOT CLOSE' -ForegroundColor Green; venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

Start-Sleep -Seconds 2

# 3. Start Vendor Dashboard Frontend
Write-Host "[3/3] Starting Vendor Dashboard..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location 'c:\Users\USER\whatsapp bot\frontend'; Write-Host 'VENDOR DASHBOARD - DO NOT CLOSE' -ForegroundColor Green; npm run dev"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  All services launched!" -ForegroundColor Green
Write-Host ""
Write-Host "  FastAPI:    http://localhost:8000"
Write-Host "  API Docs:   http://localhost:8000/docs"
Write-Host "  Dashboard:  http://localhost:5173"
Write-Host ""
Write-Host "  Optional - run ngrok in a 4th window:"
Write-Host "  ngrok http 8000"
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
