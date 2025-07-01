REM Restarts Olex2
rem https://stackoverflow.com/questions/22558869/wait-for-process-to-end-in-windows-batch-file
:loop
tasklist /fi "pid eq %1" 2>nul | find "%1" >nul
if not errorlevel 1 (
    timeout /t 1 >nul
    goto :loop
)
rem https://stackoverflow.com/questions/5909012/windows-batch-script-launch-program-and-exit-console
start "" %2