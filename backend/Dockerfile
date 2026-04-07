FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# TODO: agregar requirements.txt con fastapi + sqlalchemy + openpyxl + httpx
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# TODO: copiar app real
# COPY app/ ./app/

EXPOSE 8000

# TODO: reemplazar por uvicorn app.main:app
CMD ["bash", "-lc", "echo 'Skeleton backend: completar Dockerfile' && sleep 3600"]

