# CONATEL — Asistente de Agenda Comercial

Este repositorio contiene la herramienta de organización inteligente para comerciales de **CONATEL**. La aplicación permite gestionar visitas, planificar agendas anuales y mantener actualizadas las planillas de clientes de forma simple y automatizada.

## 🚀 Funcionalidades Principales

-   **Creación de Agenda**: Genera automáticamente una planificación de visitas basada en la prioridad de los clientes, su ubicación geográfica (departamento) y la frecuencia necesaria de contacto.
-   **Actualización de Planilla**: Permite marcar visitas realizadas y actualizar la base de datos de Excel de manera masiva o individual.
-   **Interfaz Moderna**: Desarrollada con `CustomTkinter` para una experiencia de usuario fluida y profesional en modo oscuro.
-   **Excel-Centric**: Trabaja directamente sobre tus planillas actuales de clientes.

---

## 🛠️ Requisitos e Instalación

### Desarrolladores / Ejecución desde código

Necesitás tener instalado **Python 3.10+**.

1.  **Clonar este repositorio** y situarse en la raíz.
2.  **Instalar dependencias** usando el Makefile:
    ```bash
    make install
    ```
    *Esto instalará `customtkinter`, `pandas`, `openpyxl`, `tkcalendar`, `Pillow` y `pyinstaller`.*

3.  **Ejecutar la aplicación**:
    ```bash
    python main.py
    ```

---

## 📦 Construcción del Ejecutable (.exe)

Para distribuir la aplicación a colegas que no tienen Python instalado, podés generar un ejecutable portable para Windows utilizando el sistema de **build** incluido.

### Uso del Makefile

Podés personalizar el nombre del programa y la ubicación de salida mediante variables:

```bash
# Construcción básica (genera dist/AgendaVentas.exe)
make build app

# Construcción personalizada
make build app APP_NAME=AgendaConatel2026 OUT_DIR=/ruta/a/mi/entregable
```

**Parámetros disponibles:**
-   `APP_NAME`: El nombre que tendrá el archivo ejecutable resultante.
-   `OUT_DIR`: La carpeta donde se depositará el ejecutable final.

---

## 📂 Estructura del Proyecto

-   `main.py`: Punto de entrada de la interfaz gráfica (GUI).
-   `agenda_app/`: Lógica central (I/O de Excel, algoritmos de planificación).
-   `assets/`: Recursos visuales e íconos de la marca.
-   `requirements.txt`: Lista de dependencias de Python.
-   `Makefile`: Comandos automatizados para instalación y construcción.

---

## 📝 Notas
-   Los logs de errores se guardan automáticamente en `agenda_error.log` en caso de fallos inesperados.
-   Para limpear archivos temporales generados por la construcción, usá `make clean`.
