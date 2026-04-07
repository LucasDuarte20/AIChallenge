.PHONY: up down build logs ps

COMPOSE = docker compose

up:
	@cp -n .env.example .env 2>/dev/null || true
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

build:
	$(COMPOSE) build --no-cache

logs:
	$(COMPOSE) logs -f

ps:
	$(COMPOSE) ps

