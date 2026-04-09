#!/usr/bin/env bash
# Ejecuta la app con Wine usando Python *para Windows* (no el binario Linux).
# El .exe generado por PyInstaller en Linux NO es un programa Windows: Wine no puede abrirlo.
#
# Primera ejecución: instala Python 3.11 32-bit en un WINEPREFIX dedicado (requiere winetricks y red).
#
# Uso:
#   ./scripts/run_wine_agenda.sh
#   WINEPREFIX=~/mi-prefix ./scripts/run_wine_agenda.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

# 32-bit Wine evita el choque "WINEARCH win64 vs prefijo 32-bit" en instalaciones típicas de Ubuntu.
export WINEARCH="${WINEARCH:-win32}"
export WINEPREFIX="${WINEPREFIX:-$ROOT/.wine-agenda}"

# Instalador oficial Win32 (compatible con prefijo win32)
PY_URL="${PY_URL:-https://www.python.org/ftp/python/3.11.9/python-3.11.9.exe}"
INSTALLER_CACHED="${INSTALLER_CACHED:-$ROOT/.cache/python-3.11.9-win32.exe}"
TARGET_WIN="C:\\\\Python311"

find_installed_python() {
  local p
  p="$WINEPREFIX/drive_c/Python311/python.exe"
  [[ -f "$p" ]] && echo "$p" && return
  find "$WINEPREFIX/drive_c" -path '*/Python311/python.exe' 2>/dev/null | head -1
}

if ! command -v wine >/dev/null 2>&1; then
  echo "Falta el comando wine. Instalalo y reintentá." >&2
  exit 1
fi

mkdir -p "$ROOT/.cache"

if [[ -z "$(find_installed_python)" ]]; then
  echo "Preparando Wine en: $WINEPREFIX"
  mkdir -p "$WINEPREFIX"
  wineboot --init 2>/dev/null || true

  if command -v winetricks >/dev/null 2>&1; then
    echo "Ajustando versión de Windows a 10 (requerido por el instalador de Python 3.11)…"
    # Sin esto Wine reporta Windows 7 y el instalador sale con 'Windows 8.1 or later is required'
    winetricks -q win10 || true
  else
    echo "Aviso: instalá 'winetricks' y ejecutá: winetricks win10 en este WINEPREFIX, o el instalador de Python puede fallar." >&2
  fi

  if [[ ! -f "$INSTALLER_CACHED" ]]; then
    echo "Descargando Python para Windows (32-bit)…"
    wget -q -O "$INSTALLER_CACHED" "$PY_URL" || curl -fsSL -o "$INSTALLER_CACHED" "$PY_URL"
  fi

  echo "Instalando Python en Wine (solo la primera vez, puede tardar)…"
  wine "$INSTALLER_CACHED" /quiet InstallAllUsers=0 "TargetDir=$TARGET_WIN" PrependPath=1 Include_pip=1 Include_test=0 Shortcuts=0 || {
    echo "Falló el instalador. Si el log dice 'Windows 8.1 or later', ejecutá: WINEPREFIX=$WINEPREFIX winetricks win10" >&2
    exit 1
  }
  sleep 2
fi

PYEXE="$(find_installed_python)"
if [[ -z "$PYEXE" || ! -f "$PYEXE" ]]; then
  echo "No se encontró python.exe. Borrá $WINEPREFIX y reintentá." >&2
  exit 1
fi

echo "Python Wine: $PYEXE"

if ! wine "$PYEXE" -c "import openpyxl" 2>/dev/null; then
  echo "Instalando openpyxl…"
  wine "$PYEXE" -m pip install -q --disable-pip-version-check openpyxl
fi

export PYTHONPATH="$ROOT"
export PYTHONUNBUFFERED=1
export WINEDLLOVERRIDES="${WINEDLLOVERRIDES:-winemenubuilder.exe=d}"

# main.py vía ruta Unix (Wine suele mapear Z: -> /)
MAIN_UNIX="$ROOT/main.py"
echo "Lanzando Agenda (cerrá la ventana para salir). Si se cierra sola, revisá: $ROOT/agenda_error.log"

exec wine "$PYEXE" "$MAIN_UNIX" "$@"
