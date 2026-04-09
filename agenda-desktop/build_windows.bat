@echo off
cd /d "%~dp0"

echo Instalando dependencias...
python -m pip install -r requirements.txt

echo Empaquetando con PyInstaller...
python -m PyInstaller --onefile --windowed --name AgendaVentas ^
  --hidden-import=openpyxl.cell._writer ^
  --hidden-import=babel.numbers ^
  --collect-all customtkinter ^
  --add-data "assets;assets" ^
  main.py

echo.
echo   Ejecutable en dist\AgendaVentas.exe
echo.
pause
