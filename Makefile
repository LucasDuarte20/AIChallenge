# Asistente de Agenda Comercial - Makefile
# Genera el ejecutable portable para Windows (o Linux)

# Variables configurables (se pueden pasar por línea de comandos)
# Ejemplo: make build app APP_NAME=MiAgenda OUT_DIR=./dist
APP_NAME ?= AgendaVentas
OUT_DIR ?= ./dist

.PHONY: all help install build app clean

help:
	@echo "Comandos disponibles:"
	@echo "  make install             Instala dependencias (pip)"
	@echo "  make build app           Construye el ejecutable (.exe)"
	@echo "  make clean               Limpia archivos temporales de construcción"
	@echo ""
	@echo "Variables:"
	@echo "  APP_NAME                 Nombre de la aplicación final (default: AgendaVentas)"
	@echo "  OUT_DIR                  Directorio de salida (default: ./dist)"

install:
	pip install -r requirements.txt pyinstaller

build:
	@echo "Preparando entorno de construcción..."
	@mkdir -p $(OUT_DIR)

app:
	@echo "Construyendo ejecutable: $(APP_NAME)..."
	python3 -m PyInstaller --onefile --windowed --name $(APP_NAME) \
		--hidden-import=openpyxl.cell._writer \
		--hidden-import=babel.numbers \
		--collect-all customtkinter \
		--add-data "assets:assets" \
		main.py
	@echo "Moviendo ejecutable a $(OUT_DIR)..."
	@mv dist/$(APP_NAME).exe $(OUT_DIR)/ 2>/dev/null || mv dist/$(APP_NAME) $(OUT_DIR)/ 2>/dev/null
	@echo "-------------------------------------------------------"
	@echo "✅ PROCESO FINALIZADO"
	@echo "📍 El ejecutable se encuentra en: $(OUT_DIR)/$(APP_NAME)"
	@echo "-------------------------------------------------------"

clean:
	rm -rf build/ dist/ *.spec agenda_error.log stderr.log wine.log
