@echo off
setlocal
pushd "%~dp0"
echo [dndrollbot] Working directory: %CD%

:: Check venv — expect Python 3.14
if not exist ".venv\Scripts\python.exe" (
    echo [dndrollbot] ERROR: .venv not found. Create it with: py -3.14 -m venv .venv
    echo [dndrollbot]        then: .venv\Scripts\pip install -r requirements.txt
    popd & pause & exit /b 1
)
if not exist ".venv\Scripts\activate.bat" (
    echo [dndrollbot] ERROR: .venv\Scripts\activate.bat missing — recreate venv
    popd & pause & exit /b 1
)

call ".venv\Scripts\activate.bat"
echo [dndrollbot] Python:
".venv\Scripts\python.exe" -c "import sys; print(sys.version); print(sys.executable)"

:: Quick sanity: check DISCORD_TOKEN is set (from .env or env)
".venv\Scripts\python.exe" -c "from config import load_settings; s=load_settings(); print(f'[dndrollbot] token OK ({len(s.token)} chars) guild={s.guild_id} log={s.log_level}')" 2>nul
if %ERRORLEVEL% neq 0 (
    echo [dndrollbot] WARNING: DISCORD_TOKEN not configured — see .env.example
)

echo [dndrollbot] Starting bot...
".venv\Scripts\python.exe" main.py
set RC=%ERRORLEVEL%
echo [dndrollbot] exited with code %RC%
popd
pause
exit /b %RC%
