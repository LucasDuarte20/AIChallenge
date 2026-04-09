#!/usr/bin/env bash
# Importa un Excel directamente via API REST (sin entrar al contenedor)
set -euo pipefail

FILE="${1:-}"
SHEET="${2:-Sheet1}"
API_URL="${API_URL:-http://localhost:8000}"

if [[ -z "$FILE" ]]; then
  echo "Uso: ./scripts/import_excel.sh <archivo.xlsx> [nombre_hoja]"
  echo "El archivo debe estar en ./data/"
  exit 1
fi

if [[ ! -f "data/$FILE" ]]; then
  echo "ERROR: data/$FILE no encontrado"
  exit 1
fi

echo "Importando '$FILE' (hoja: $SHEET)..."

curl -s -X POST "$API_URL/import-excel" \
  -F "file=@data/$FILE" \
  -F "sheet_name=$SHEET" | python3 -m json.tool

echo ""
echo "Listo."
