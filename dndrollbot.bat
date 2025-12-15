@echo off
setlocal
pushd "%~dp0"
echo [dndrollbot] Working directory: %CD%
echo [dndrollbot] Activating virtual environment from .venv\Scripts\activate.bat
if exist ".venv\Scripts\activate.bat" (
	call ".venv\Scripts\activate.bat"
) else (
	echo [dndrollbot] ERROR: Virtual environment not found at .venv\Scripts\activate.bat
	popd
	pause
	exit /b 1
)
echo [dndrollbot] Python executable being used:
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -c "import sys; print(sys.executable)"
) else (
    python -c "import sys; print(sys.executable)"
)

echo [dndrollbot] Running: using venv python if available
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    python main.py
)
set RC=%ERRORLEVEL%
echo [dndrollbot] python exited with code %RC%
popd
pause
exit /b %RC%