import os
import sys
import platform
import subprocess

os_name = platform.system()

if os_name != "Windows":
    print("This game is only supported on window currently!")
    sys.exit()
    
directory = os.path.dirname(os.path.realpath(__file__))

os.chdir(directory)
    
if not (os.path.exists("venv") and os.path.isdir("venv")):
    print("Setting up virtual environment... It could take a few seconds...")
    subprocess.call(r"python -m venv venv", shell=True)
    
if sys.platform.startswith('win'): # window shells
    subprocess.call(r".\venv\Scripts\activate", shell=True, executable="cmd.exe") # windows use slash as path separator (/); Also, cmd is the specified shell to avoid powershell-related virtualenv issues
elif sys.platform.startswith('linux') or sys.platform.startswith('darwin'): # unix-like shells
    subprocess.call(r"source ./venv/bin/activate", shell=True) # unix-like shells use backslash as path separator (\)
else:
    print("Unknown shell")
    sys.exit()
    
installed_packages = set(map(str.strip, subprocess.check_output(['pip', 'freeze']).decode('utf-8').split('\n')))
with open("requirements.txt", "r") as required_packages:
    for line in required_packages:
        required_package_name = line.strip()
        if required_package_name not in installed_packages:
            subprocess.call(rf"pip install {required_package_name}", shell=True)

    