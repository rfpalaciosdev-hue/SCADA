FROM python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema para psycopg2
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requerimientos e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar todo el código (backend, bridge, simulator)
COPY . .
# También necesitamos historian_bridge.py o separarlos? 
# Por ahora pondremos el backend solo.

EXPOSE 8000

CMD ["python", "backend_api.py"]
