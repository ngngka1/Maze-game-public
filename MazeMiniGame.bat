@echo off
setlocal EnableDelayedExpansion

if not "%OS%" == "Windows_NT" (
    echo This game is only supported on window for now!
    timeout /t 5 > nul
    exit
)

dir /b /ad | findstr /i /x /c:"venv" > nul
if !errorlevel! neq 0 (
    echo Installing virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat

for /F "tokens=*" %%A in (requirements.txt) do (
    pip freeze | findstr /i /x /c:"%%A"
    if !errorlevel! neq 0 (
        echo installing %%A...
        pip install %%A
    )
)

python main.py
call venv\Scripts\dectivate.bat