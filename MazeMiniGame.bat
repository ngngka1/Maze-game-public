@echo off
setlocal EnableDelayedExpansion

REM check if target computer is window
if not "%OS%" == "Windows_NT" (
    echo This game is only supported on window for now!
    timeout /t 5 > nul
    exit
)

REM check if virtual environment is installed
dir /b /ad | findstr /i /x /c:"venv" > nul
if !errorlevel! neq 0 (
    echo Installing virtual environment...
    python -m venv venv
)

pushd .
cd venv

REM check if shells runned is tradiation window shells (cmd/powershell) OR unix-like shells(bash etc.)
dir /b /ad | findstr /i /x /c:"Scripts" > nul 
if !errorlevel! == 0 (
    call ./Scripts/activate.bat
    if !errorlevel! neq == 0 (
        call ./Scripts/Activate.ps1
    )
) else ( 
    dir /b /ad | findstr /i /x /c:"bin" > nul 
    if !errorlevel! == 0 (
        echo game runned with unix-like shells
        source ./bin/activate
    )
    else (
        echo error: no virtual environment executables directory found
        timeout /t 5 > nul
        exit
    )
)

popd



for /F "tokens=*" %%A in (requirements.txt) do (
    python -m pip freeze | findstr /i /x /c:"%%A"
    if !errorlevel! neq 0 (
        echo installing %%A...
        python -m pip install %%A
    )
)

python main.py

REM try to deactivate virtualenv with cmd command, if fail, run with powershell command
call venv\Scripts\deactivate.bat
if !errorlevel! neq == 0 (
    deactivate
)