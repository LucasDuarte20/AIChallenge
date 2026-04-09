# 🚀 Guía para Compañeros — Asistente de Agenda Comercial CONATEL

> Esta guía es para **todos** en el equipo: vendedores que usan la app, y compañeros del challenge que quieran tocar el código.

---

## 📋 ¿Qué hace esta app?

Imaginá que tenés **200 clientes** y tenés que organizar qué clientes visitar cada día, en qué orden, cuándo fue la última vez que hablaste con cada uno, y a quién le toca próximamente. Hacerlo manualmente es un embole.

**Esta app lo hace automáticamente:**

1. **Prioriza** quién necesita una visita urgente:
   - Clientes grandes y de alto potencial primero
   - Clientes que hace mucho no visitás reciben más prioridad
   - Clientes sin visita previa se agendan urgente

2. **Agrupa** visitas por departamento y cercanía geográfica para no ir de un lado a otro

3. **Genera una agenda** con días, horarios y clientes ya organizados en formato Excel

4. **Actualiza** tu planilla con las fechas de última y próxima visita

---

## 🖥️ ¿Cómo uso la app?

### El ejecutable (.exe)

La app viene como un archivo `AgendaVentas.exe`. **No necesitás instalar nada:**

1. Descargá el `.exe` (o recibilo de un compañero)
2. Doble click para abrir
3. Si Windows lo bloquea: click en **"Más información"** → **"Ejecutar igualmente"**

> ⚠️ **En Linux**, ejecutá con: `python3 main.py` (o con Wine si querés probar el .exe)

### Flujo de trabajo semanal recomendado

```
📅 Viernes al final de la semana:

1. Abrí la app
2. "Actualizar Planilla" → marcá los clientes que visitaste esta semana
3. "Crear Agenda" → generá la agenda para la semana siguiente
4. Imprimí o revisá tu agenda nueva para el lunes

→ Repetir cada semana 🔁
```

---

### 📅 Crear Agenda — Paso a paso

1. Abrí la app y hacé click en **"Crear Agenda"**
2. Se abre un diálogo para seleccionar tu **planilla Excel** de clientes
3. En la ventana de configuración:
   - **Vendedor**: Elegí tu código de vendedor
   - **Fecha de inicio**: Seleccioná en el calendario cuándo empieza la agenda
   - **Visitas por día**: Ajustá con el slider (ej: 3 visitas por día)
   - **Duración**: Cuántas semanas (ej: 1 para la próxima semana)
4. Click en **"🚀 Generar Agenda"**
5. Revisá la **vista previa** a la derecha:
   - Estadísticas: total de visitas, clientes y días
   - Lista de visitas agrupadas por día
6. Click en **"💾 Guardar Excel"**
7. Elegí dónde guardarlo

**¿Qué genera?** Un Excel con:
- Tu planilla original con las **fechas de próxima visita** actualizadas
- Hoja **"Agenda"**: listado completo de visitas con fecha, día, hora, cliente
- Hoja **"Vista Semanal"**: formato de agenda semanal (filas=hora, columnas=lunes-viernes)

---

### 📝 Actualizar Planilla — Paso a paso

1. Abrí la app y hacé click en **"Actualizar Planilla"**
2. Seleccioná tu **planilla Excel**
3. Elegí tu **código de vendedor**
4. Click en **"Cargar"** para ver los clientes
5. Para cada cliente que visitaste:
   - Escribí la fecha en formato **AAAA-MM-DD** (ej: 2026-04-09)
   - O hacé click en **"Hoy"** para poner la fecha de hoy
   - O usá **"📅 Marcar todos hoy"** si visitaste a todos
6. Click en **"💾 Guardar cambios"**
7. Elegí dónde guardar la planilla actualizada

---

### 📊 Formato del Excel

Tu planilla debe tener una hoja llamada **"LISTA DE INDUSTRIA"** con estas columnas:

| Columna | Descripción | Requerida |
|---|---|---|
| N. Cli. | Número de cliente | No |
| Nombre | Nombre del cliente | **Sí** |
| Departamento | Departamento/estado | No (pero mejora la agenda) |
| Dirección | Dirección física | **Sí** |
| Tipo | chico / medio / grande | No (asume medio) |
| Potencial | bajo / medio / alto | No (asume medio) |
| Teléfono | Teléfono de contacto | No |
| Oficina | Código de oficina | No |
| Vendedor | Código del vendedor | **Sí** |
| Sector | Sector del cliente | No |
| Latitud / Longitud | Coordenadas GPS | No (pero mejora cercanía) |

> La app agrega automáticamente las columnas **"Fecha última visita"** y **"Fecha próxima visita"** si no existen.

#### ¿Cómo se calculan las prioridades?

La app usa una **matriz de frecuencia** según tipo y potencial:

| Tipo \ Potencial | Alto | Medio | Bajo |
|---|---|---|---|
| **Grande** | 12 visitas/año | 6 | 4 |
| **Medio** | 6 | 4 | 2 |
| **Chico** | 4 | 2 | 1 |

Y además considera cuánto tiempo pasó desde la última visita: a mayor tiempo, mayor urgencia.

---

## 🛠️ Para los que quieren tocar el código

### Requisitos

1. **Python 3.11** o superior → [python.org/downloads](https://www.python.org/downloads/)
   - Al instalar, **marcar "Add to PATH"**
2. **Git** → [git-scm.com](https://git-scm.com/)
3. **Un editor** → VS Code (recomendado) o el que quieras

### Instalación del entorno

```bash
# 1. Clonar el repositorio (o descargarlo como .zip)
git clone <URL_DEL_REPO>
cd AIChallenge/agenda-desktop

# 2. Crear entorno virtual
python -m venv venv

# 3. Activar el entorno
# En Windows (CMD):
venv\Scripts\activate
# En Windows (PowerShell):
venv\Scripts\Activate.ps1
# En Linux/Mac:
source venv/bin/activate

# 4. Instalar dependencias
pip install -r requirements.txt

# 5. Ejecutar la app
python main.py
```

### Estructura del código

```
agenda-desktop/
├── main.py                  # 🖥️  La interfaz de usuario (CustomTkinter)
├── agenda_app/
│   ├── models.py            # 📦  Modelo de datos (ClientRow)
│   ├── excel_io.py          # 📊  Lectura/escritura de Excel + hojas de agenda
│   └── planner.py           # 🧠  Lógica de planificación (urgencia, cercanía, frecuencia)
├── assets/
│   └── conatel_logo.png     # 🎨  Logo de Conatel (colocar aquí el PNG)
├── requirements.txt         # 📋  Dependencias de Python
├── build_windows.bat        # 🔨  Script para generar el .exe (Windows)
├── build_windows.sh         # 🔨  Script para generar el .exe (Linux/Wine)
├── AgendaVentas.spec        # ⚙️  Configuración de PyInstaller
└── data/                    # 📁  Archivos Excel de ejemplo
```

#### ¿Dónde vive cada cosa?

- **¿Quiero cambiar cómo se ve la app?** → `main.py` (colores, layout, textos)
- **¿Quiero cambiar la lógica de priorización?** → `planner.py` (function `_priority_score`, `_visits_per_year`, `scheduling_urgency`)
- **¿Quiero agregar una columna del Excel?** → `excel_io.py` (agregar alias en `FIELD_ALIASES`) + `models.py` (agregar campo a `ClientRow`)
- **¿Quiero cambiar el formato del Excel exportado?** → `excel_io.py` (functions `write_agenda_flat_sheet`, `write_weekly_agenda_sheet`)

### Hacer cambios

1. Abrí el proyecto en VS Code (o con Antigravity)
2. Hacé tus cambios en los archivos `.py`
3. Probá ejecutando `python main.py`
4. Si funciona bien, ¡generá el nuevo .exe!

### Usando Antigravity (IA)

Si tenés la extensión Antigravity en VS Code, podés:

1. Abrir el proyecto en VS Code
2. Abrir el chat de Antigravity
3. Pedirle que haga cambios en lenguaje natural:
   - _"Cambiá el color del botón de rojo a azul"_
   - _"Agregá un campo 'email' al Excel"_
   - _"Mostrá el teléfono del cliente en la vista previa"_
4. La IA modifica el código por vos
5. Probá con `python main.py`
6. Si funciona, generá el .exe

---

## 📦 Generar el .exe (PyInstaller)

### En Windows (forma más fácil)

```cmd
cd agenda-desktop
build_windows.bat
```

El ejecutable queda en **`dist\AgendaVentas.exe`** (~20-30 MB).

### En Linux (cross-compile — solo si no tenés Windows)

```bash
cd agenda-desktop
bash build_windows.sh
```

> ⚠️ Nota: El .exe generado desde Linux funciona en Windows. Si querés probarlo en Linux, usá `python3 main.py` directamente.

### Manualmente (si los scripts no funcionan)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name AgendaVentas \
  --hidden-import=openpyxl.cell._writer \
  --hidden-import=babel.numbers \
  --collect-all customtkinter \
  --add-data "assets:assets" \
  main.py
```

En Windows, reemplazá `assets:assets` por `assets;assets` (`;` en vez de `:`).

---

## 🐛 Problemas comunes

### "Windows protegió tu equipo"
- Click en **"Más información"** → **"Ejecutar igualmente"**
- Pasa porque el .exe no está firmado digitalmente (es normal)

### "No module named customtkinter" (al ejecutar `python main.py`)
```bash
pip install -r requirements.txt
```

### El calendario no muestra los días en español
```bash
pip install babel
```

### "Hoja no encontrada" al cargar el Excel
- Tu planilla debe tener una hoja llamada **"LISTA DE INDUSTRIA"**
- Si se llama distinto, hay que cambiar la constante `CLIENTS_SHEET_DEFAULT` en `agenda_app/excel_io.py`

### El .exe se cierra solo al abrirlo
- Buscá el archivo `agenda_error.log` al lado del `.exe`
- Ahí encontrás el error detallado

### La app se ve gris/fea (sin tema dark)
- Asegurate de tener `customtkinter` instalado: `pip install customtkinter`
- Si el .exe se ve mal, regeneralo con `build_windows.bat`

### No me aparece el logo de Conatel
- Colocá el archivo `conatel_logo.png` en la carpeta `assets/`
- Al generar el .exe, asegurate de usar `--add-data "assets:assets"` (ya está en los scripts)
- Si no hay logo, la app muestra "CONATEL" en texto rojo (funciona igual)

---

## 📂 La app web (Docker) — para referencia

El repositorio también tiene una versión web con Docker Compose (backend FastAPI + frontend + PostgreSQL). Si querés usarla:

```bash
# En la raíz del repo (no en agenda-desktop)
cd AIChallenge

# Copiar configuración
cp .env.example .env

# Levantar todo
make up

# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

Pero para el uso diario del vendedor, la **app de escritorio** es lo más práctico.

---

## 📞 ¿Dudas?

Si algo no te funciona:
1. Revisá esta guía
2. Buscá el `agenda_error.log`
3. Consultá con el equipo en el canal del challenge

¡Buena suerte! 💪
