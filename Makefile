.PHONY: help up down build logs shell-backend import-excel seed reset-db ps clean

COMPOSE = docker compose
BACKEND = stock_backend

help:
	@echo ""
	@echo "  Chatbot de Stock - Comandos disponibles"
	@echo "  ----------------------------------------"
	@echo "  make up            Levantar todos los servicios"
	@echo "  make up-ollama     Levantar incluyendo Ollama"
	@echo "  make down          Detener todos los servicios"
	@echo "  make build         Reconstruir imágenes"
	@echo "  make logs          Ver logs de todos los servicios"
	@echo "  make logs-backend  Ver logs del backend"
	@echo "  make shell-backend Abrir shell en el backend"
	@echo "  make import-excel  Importar Excel desde ./data/"
	@echo "  make seed          Insertar datos de ejemplo"
	@echo "  make reset-db      Borrar y recrear la base de datos"
	@echo "  make ps            Estado de contenedores"
	@echo "  make clean         Borrar volúmenes y contenedores"
	@echo "  make up-telegram   Levantar bot gratis Telegram"
	@echo "  make up-sync       Levantar sync SharePoint"
	@echo ""

up:
	@cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) up -d
	@echo ""
	@echo "  Servicios activos:"
	@echo "  - Backend API:  http://localhost:$${BACKEND_PORT:-8000}"
	@echo "  - Frontend:     http://localhost:$${FRONTEND_PORT:-3000}"
	@echo "  - Adminer:      http://localhost:$${ADMINER_PORT:-8080}"
	@echo ""

up-ollama:
	@cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) --profile ollama up -d
	@echo "  Ollama: http://localhost:$${OLLAMA_PORT:-11434}"

up-telegram:
	@cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) --profile telegram up -d

up-sync:
	@cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) --profile sync up -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build --no-cache

logs:
	$(COMPOSE) logs -f

logs-backend:
	$(COMPOSE) logs -f backend

logs-db:
	$(COMPOSE) logs -f postgres

shell-backend:
	docker exec -it $(BACKEND) bash

import-excel:
	@if [ -z "$(FILE)" ]; then \
		echo "Uso: make import-excel FILE=nombre_archivo.xlsx"; \
		echo "El archivo debe estar en ./data/"; \
	else \
		docker exec $(BACKEND) python -m app.scripts.import_excel $(FILE); \
	fi

seed:
	docker exec $(BACKEND) python -m app.scripts.seed_example

reset-db:
	$(COMPOSE) down -v
	$(COMPOSE) up -d postgres
	@echo "Base de datos reiniciada."

ps:
	$(COMPOSE) ps

clean:
	$(COMPOSE) down -v --remove-orphans
	docker image prune -f
