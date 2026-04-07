# AIChallenge

Repositorio de código para desafío AI de Conatel S.A.

## Agenda de visitas (pseudo-esqueleto)

Este directorio es una **base guía** para que el equipo reconstruya la solución completa con Cursor / Antigravity.

### Objetivo

- Importar un Excel de clientes (vendedor, dirección, tipo, potencial).
- Geolocalizar direcciones (lat/lon) para optimizar rutas.
- Generar agenda por vendedor **desde hoy + 14 días** por 1 año.
- Exportar un Excel “agenda” por vendedor.

### Estructura

```
.
  docker-compose.yml
  .env.example
  Makefile
  README.md
  backend/
  data/
  scripts/
```

### Estado

- El skeleton **no está completo a propósito**: es una guía para implementar.
- Podés usar como referencia una implementación funcional en otro entorno de trabajo si la tenés.

### Primeros pasos (local)

```bash
cp .env.example .env
docker compose up -d
```

Luego completar `backend/` según el prompt del equipo.
