@echo off
setlocal

cd /d "%~dp0"
echo [T1] repo = %cd%

REM ---- pick a real python.exe if possible ----
set "PYEXE="

for /f "delims=" %%i in ('where python.exe 2^>nul') do (
  set "PYEXE=%%i"
  goto :FOUND_PY
)

:FOUND_PY
if not defined PYEXE (
  echo [T2] python.exe not found, fallback to python (may be .bat)
  where python >nul 2>nul
  if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    pause
    exit /b 1
  )
  set "PYEXE=python"
) else (
  echo [T2] Using python.exe: %PYEXE%
)

echo [T3] Python version check...
call %PYEXE% -V
echo [T4] after -V

if not exist ".venv" (
  echo [T5] Creating venv...
  call %PYEXE% -m venv .venv
  if errorlevel 1 (
    echo [ERROR] venv creation failed.
    pause
    exit /b 1
  )
) else (
  echo [T5] venv already exists.
)

echo [T6] checking activate.bat...
if not exist ".venv\Scripts\activate.bat" (
  echo [ERROR] Missing .venv\Scripts\activate.bat
  pause
  exit /b 1
)

echo [T7] Activating venv...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
  echo [ERROR] venv activate failed.
  pause
  exit /b 1
)

echo [T8] which python?
where python
python -V

echo [T9] pip upgrade...
python -m pip install -U pip
if errorlevel 1 (
  echo [ERROR] pip upgrade failed.
  pause
  exit /b 1
)

echo [T10] install requirements...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] requirements install failed.
  pause
  exit /b 1
)

echo [T11] editable install...
python -m pip install -e .
if errorlevel 1 (
  echo [ERROR] editable install failed.
  pause
  exit /b 1
)

echo [T12] run benchmark...
python -m obrbr --config configs\bench.yaml
if errorlevel 1 (
  echo [ERROR] benchmark run failed.
  pause
  exit /b 1
)

echo [DONE] check results\YYYYMMDD_HHMM\
pause
endlocal
