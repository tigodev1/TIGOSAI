@echo off

echo Installing required Python libraries...
python -m pip install -r requirements.txt

echo Building the executable file...
pyinstaller --onefile --windowed --icon=Assets/icon.ico --add-data "Assets;Assets" --name "TigosProjects1" main.py

echo.
echo Build complete. The executable is in the "dist" folder.
pause