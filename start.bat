@echo off
echo ==============================================
echo Iniciando o Prospect Automator
echo ==============================================

echo Iniciando o Backend FastAPI (Python)...
cd backend
start cmd /k ".\venv\Scripts\activate.bat && python main.py"

echo Iniciando o Frontend React (Vite)...
cd ..\frontend
start cmd /k "npm run dev"

echo Pronto! Os servidores estao rodando.
echo O frontend geralmente roda em http://localhost:5173
echo O backend em http://localhost:8000
