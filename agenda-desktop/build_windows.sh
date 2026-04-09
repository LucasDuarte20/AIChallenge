#!/usr/bin/env bash
# Genera AgendaVentas.exe en dist/ (ejecutar en Windows o cross-compile desde Linux con wine).
set -euo pipefail
cd "$(dirname "$0")"

echo "Instalando dependencias..."
python3 -m pip install -q -r requirements.txt

echo "Empaquetando con PyInstaller..."
python3 -m PyInstaller --onefile --windowed --name AgendaVentas \
  --hidden-import=openpyxl.cell._writer \
  --hidden-import=babel.numbers \
  --collect-all customtkinter \
  --add-data "assets:assets" \
  main.py

echo ""
echo "  ✅ Ejecutable generado en: dist/AgendaVentas.exe"
echo ""
