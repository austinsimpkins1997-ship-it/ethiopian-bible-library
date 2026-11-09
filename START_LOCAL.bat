@echo off
setlocal
cd /d "%~dp0"

py -3 -V >nul 2>&1
if not errorlevel 1 (
  py -3 -B start_local_server.py
  goto :done
)

python -V >nul 2>&1
if not errorlevel 1 (
  python -B start_local_server.py
  goto :done
)

echo Python 3 is required to start the local reader.
echo Install Python 3, then double-click START_LOCAL.bat again.
pause
exit /b 1

:done
endlocal
