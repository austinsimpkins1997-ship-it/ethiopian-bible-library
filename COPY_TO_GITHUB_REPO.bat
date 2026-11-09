@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0COPY_TO_GITHUB_REPO.ps1" %*
if errorlevel 1 (
  echo.
  echo The copy did not complete. Read the message above.
  pause
)
endlocal
