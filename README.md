# MVP Local Dockerizado — Agenda de Visitas (IA) + (Legacy: Stock Chat)

Este repo ahora incluye un **MVP de agenda anual de visitas para comerciales**, generado a partir de una planilla Excel de clientes y optimizado por cercanía de direcciones (geocoding + heurísticas).

> El módulo de “Stock Chat” quedó en el repo como base reutilizable, pero el foco actual es **Agenda**.

## Stack

| Componente | Tecnología |
|---|---|
| Base de datos | PostgreSQL 16 |
| Admin DB | Adminer |
| Backend | Python 3.12 + FastAPI |
| Frontend | HTML/CSS/JS vanilla + Nginx |
| LLM | Ollama (local) / OpenAI (futuro) / Mock (default) |
| Orquestación | Docker Compose |

---

## Requisitos

- Docker + Docker Compose v2
- `make` (opcional pero recomendado)

---

## Levantar el entorno

```bash
# 1. Clonar / entrar al directorio
cd aichallenge

# 2. Copiar configuración (se copia automático con make up)
cp .env.example .env

# 3. Levantar todo
make up
```

Servicios disponibles:

| Servicio | URL |
|---|---|
| Frontend (chat) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger / docs | http://localhost:8000/docs |
| Adminer | http://localhost:8080 |

---

## Agenda de Visitas (nuevo)

### 1) Importar Excel de clientes

El Excel puede tener encabezados en **fila 2 o 3** (el backend **auto-detecta** si usás `header_row_index=0`).

Columnas soportadas (las que encuentre en la fila de encabezados):
- `N. Cli.`, `Nombre` o `1. Nombre`, `Departamento` (opcional), `Dirección`, `Tipo`, `Potencial`, `Teléfono`, `Oficina`, `Vendedor`, `Sector` (opcional)

```bash
curl -X POST http://localhost:8000/clients/import-excel \
  -F "file=@./data/clients.xlsx" \
  -F "sheet_name=LISTA DE INDUSTRIA" \
  -F "header_row_index=0"
```

Si querés forzar la fila de encabezados: `-F "header_row_index=2"` o `3`.

### 2) Geocodificar direcciones (para rutas eficientes)

Este MVP usa **Nominatim (OpenStreetMap)** (gratis) para transformar `Dirección` → lat/lon y estimar `department`.

Ejemplo (batch chico):

```bash
curl -X POST "http://localhost:8000/geocode/run?batch_size=30&delay_seconds=0.2"
```

Recomendación: correrlo en batches hasta completar la mayoría de direcciones.

### 3) Generar agenda anual por vendedor

- **Frecuencia** según Tipo/Potencial (matriz en código); si faltan datos, neutro (medio/medio).
- **Ventana**: `start_day` por defecto **hoy + 14 días**; `horizon_days` default **365**.
- **Visitas por día**: por defecto **`VISITS_PER_DAY` en `.env` (2)**. Podés sobrescribir con query `visits_per_day=`.

Generar para todos los vendedores (usa 2 visitas/día salvo que cambies `.env`):

```bash
curl -X POST "http://localhost:8000/plans/generate?year=2026"
```

Generar para un vendedor específico (ej. forzar 4 visitas ese día):

```bash
curl -X POST "http://localhost:8000/plans/generate?year=2026&executive_code=99&visits_per_day=4"
```

### 4) Exportar la agenda a Excel (uno por vendedor)

```bash
# Descarga un XLSX con columnas: Fecha, Hora, Orden, Cliente, Dirección, Departamento
curl -o agenda_99_2026.xlsx "http://localhost:8000/plans/99/export.xlsx?year=2026"
```

El backend también guarda copias en `./data/exports/`.

### 5) Ver agenda en JSON

```bash
curl "http://localhost:8000/plans/99?year=2026"
```

## Importar el Excel real (Stock Chat) (legacy)

### SharePoint (automático, recomendado para el viernes)

Si la planilla está en SharePoint y se actualiza cada ~8 horas, lo más simple es:
**sincronizarla automáticamente** y responder consultas desde el celular por **Telegram**.

#### 1) Crear un bot gratis en Telegram

- En Telegram buscá `@BotFather`
- Ejecutá `/newbot`
- Copiá el token y ponelo en `.env`:

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
```

#### 2) Configurar descarga desde SharePoint (Microsoft Graph)

Para bajar el Excel desde SharePoint de forma server-to-server necesitás una app en Azure AD
con credenciales (client credentials).

En `.env` completá:

```env
SP_TENANT_ID=...
SP_CLIENT_ID=...
SP_CLIENT_SECRET=...
SP_SHARE_URL=https://... (link de “Compartir” del Excel)
SP_SHEET_NAME=Sheet1
SYNC_ENABLED=true
SYNC_INTERVAL_SECONDS=1800
```

#### 3) Levantar bot + syncer

```bash
make up
make up-sync
make up-telegram
```

- El syncer baja el archivo y lo importa a PostgreSQL cada N segundos.
- El bot de Telegram responde usando el endpoint `/chat` (mismo motor de reglas + SQL).

> Si no querés sync automático, dejá `SYNC_ENABLED=false` y seguí usando import manual.

### Opción A — Desde el frontend

1. Copiá tu archivo `.xlsx` a la carpeta `./data/`
2. Abrí http://localhost:3000
3. Hacé click en **📥 Importar Excel**
4. Seleccioná el archivo y presioná **Importar**

### Opción B — Con Make

```bash
# Primero copiá el archivo a ./data/
cp /ruta/a/tu/archivo.xlsx ./data/

make import-excel FILE=tu_archivo.xlsx
# Con hoja específica:
make import-excel FILE=tu_archivo.xlsx SHEET=Hoja1
```

### Opción C — Via curl

```bash
curl -X POST http://localhost:8000/import-excel \
  -F "file=@./data/tu_archivo.xlsx" \
  -F "sheet_name=Sheet1"
```

### Opción D — Generar Excel de ejemplo para pruebas

```bash
python3 scripts/generate_sample_excel.py
# Genera ./data/stock_ejemplo.xlsx

make import-excel FILE=stock_ejemplo.xlsx
```

### Opción E — Seed de datos mínimo (sin Excel)

```bash
make seed
```

---

## Probar búsquedas

```bash
# Buscar por código de material
curl "http://localhost:8000/materials/786518"

# Buscar por texto libre
curl "http://localhost:8000/materials/search?q=Int+Tmag"

# Buscar por MLFB
curl "http://localhost:8000/materials/search?q=5TJ6216-7"

# Stock de un material
curl "http://localhost:8000/stock?material_code=786518"

# Precio de un material
curl "http://localhost:8000/price?material_code=786518"
```

---

## Probar el chat

### Desde el frontend

Abrí http://localhost:3000 y escribí en el chat.

### Via API

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "hay stock del material 786518?"}'
```

### Ejemplos de preguntas reales

| Pregunta | Intent detectado |
|---|---|
| `hay stock del material 786518?` | stock |
| `cuanto sale el 5TJ6216-7?` | price |
| `buscame Int Tmag 06kA C 2P 16A` | material_search |
| `que materiales tienen stock pendiente?` | pending_stock |
| `que tengo que comprar?` | buy_list |
| `cual es el costo total del material 786518?` | total_cost |
| `cuantas unidades del contactor 3RT2016?` | stock |

---

## Configurar LLM

### Modo mock (default) — sin LLM, solo reglas

```env
LLM_PROVIDER=mock
```

### Modo Ollama — LLM local gratuito

```bash
# 1. Levantar con Ollama
make up-ollama

# 2. Descargar modelo (dentro del contenedor)
docker exec -it stock_ollama ollama pull llama3.2

# 3. Configurar en .env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3.2
```

### Modo OpenAI (preparado, no implementado aún)

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

> El adaptador OpenAI está como placeholder en `backend/app/services/llm_service.py`.

---

## Estructura del proyecto

```
aichallenge/
├── docker-compose.yml
├── .env.example
├── Makefile
├── README.md
├── data/                        # Archivos Excel (montado en /app/data)
├── db/
│   └── init.sql                 # Extensiones PostgreSQL (pg_trgm)
├── scripts/
│   ├── import_excel.sh          # Importación via API REST
│   └── generate_sample_excel.py # Genera Excel de ejemplo
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py              # Entry point FastAPI
│       ├── core/config.py       # Variables de entorno
│       ├── models/
│       │   ├── database.py      # Engine + Session SQLAlchemy
│       │   └── tables.py        # Modelos ORM
│       ├── schemas/             # Pydantic schemas (request/response)
│       ├── repositories/        # Acceso a datos (SQL)
│       ├── services/
│       │   ├── import_service.py
│       │   ├── search_service.py
│       │   ├── chat_service.py
│       │   ├── llm_service.py   # Abstracción LLM (mock/ollama/openai)
│       │   └── audio_service.py # Abstracción transcripción
│       ├── utils/
│       │   ├── excel_parser.py  # Parsing robusto del Excel
│       │   └── intent_detector.py # Detección de intención por reglas
│       ├── api/routes/          # Endpoints FastAPI
│       └── scripts/             # CLIs de mantenimiento
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── index.html
    ├── style.css
    └── app.js
```

---

## Schema de base de datos

### `materials_stock`
Contiene todos los materiales importados. Upsert por `material_code + material_mlfb`.

### `import_jobs`
Historial de importaciones: status, filas procesadas, errores.

### `query_logs`
Log de todas las consultas del chat: intent detectado, entidades extraídas, respuesta.

---

## Decisiones técnicas

### Por qué SQLAlchemy sync y no async
Para un MVP con carga baja, la versión síncrona es más simple de debuggear y no tiene gotchas con sesiones. Se puede migrar a `asyncpg` + `AsyncSession` si escala.

### Por qué vanilla JS y no React
Cero dependencias frontend = cero problemas de versiones, builds y node_modules. El frontend es estático y simple de entender.

### Por qué rapidfuzz para fuzzy search
Permite buscar por nombre parcial ("Int Tmag") cuando el usuario no recuerda el código exacto. Complementa a ILIKE de PostgreSQL.

### Por qué LLM_PROVIDER=mock por defecto
La detección por reglas cubre el 95% de los casos con código limpio y sin latencia de LLM. El LLM solo mejora casos de baja confianza cuando está disponible.

### Upsert strategy
Se identifica un material por `(material_code, material_mlfb)`. Si ya existe, se actualizan todos los campos. Esto permite reimportar el mismo Excel sin duplicar datos.

---

## Próximos pasos

### Integrar Qlik automático
1. Crear un endpoint `POST /import-qlik` que acepte webhook de Qlik o credenciales de API.
2. Implementar `QlikDataSource` en `services/` que descargue la hoja programáticamente.
3. Agregar un scheduler (APScheduler o Celery Beat) para importación periódica.
4. Ver rama futura: `feature/qlik-integration`.

### Integrar WhatsApp
WhatsApp oficial (Meta Cloud) no es “gratis”. Para un MVP rápido y sin costo, Telegram suele ser mejor.
Si igual quieren WhatsApp:

1. Opción oficial: Meta Cloud API (pago).
2. Opción no oficial: “web automation” (riesgo de bloqueo; no recomendado para producción).
3. En ambos casos: webhook `POST /webhook/whatsapp` que reusa `process_chat()`.

### Integrar audio real
1. Cambiar `LLM_PROVIDER=openai` y agregar `OPENAI_API_KEY`.
2. El adaptador `OpenAIWhisperTranscriber` en `audio_service.py` está listo para completar.
3. Alternativa local: agregar servicio `whisper` en docker-compose con `faster-whisper`.

### Otras mejoras
- Autenticación básica (API key en headers)
- Paginación en listados grandes
- Gráficos de stock en el frontend
- Notificaciones cuando stock baja de umbral
- Soporte multi-empresa / multi-depósito

### Mejoras Agenda (recomendadas)
- Agregar columnas en Excel: `tipo_cliente` (chico/mediano/grande) y `potencial` (bajo/medio/alto)
- Frecuencias: grande/alto más visitas, chico/bajo menos
- “Rolling replanning”: recalcular solo próximas 2–4 semanas al cambiar la planilla
- Export `.ics` para importar en Outlook (paso siguiente rápido)

---

## Comandos útiles

```bash
make up              # Levantar servicios
make up-ollama       # Levantar con Ollama
make down            # Detener servicios
make logs-backend    # Ver logs del backend
make shell-backend   # Shell interactivo en el backend
make seed            # Insertar datos de ejemplo
make reset-db        # Resetear base de datos completa
make clean           # Borrar todo (incluye volúmenes)
```
