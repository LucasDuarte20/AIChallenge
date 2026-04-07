# Backend (Skeleton)

## Endpoints que deberían existir

- `POST /clients/import-excel` (subir Excel de clientes)
- `POST /geocode/run` (geocodificar direcciones faltantes)
- `POST /plans/generate` (generar agenda por vendedor desde hoy+14 por 1 año)
- `GET /plans/{executive_code}/export.xlsx` (exportar agenda a Excel)

## Servicios

- Parser de Excel que soporte headers en fila 2/3.
- Geocoder (Nominatim) con cache.
- Planner (frecuencia según tamaño/potencial + ruteo por cercanía).

