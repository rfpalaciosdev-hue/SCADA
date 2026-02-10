# Guía de Configuración y Ejecución - Proyecto SCADA

Este documento detalla cómo configurar y ejecutar el sistema SCADA completo en tu entorno local utilizando Docker.

## Prerrequisitos

Asegúrate de tener instalados:
- **Docker Engine** y **Docker Compose** (Plugin V2 `docker compose`).

## Estructura del Proyecto

El sistema se compone de varios servicios orquestados por Docker:

1.  **Frontend**: Dashboard en React/Vite (Puerto 5173).
2.  **Backend API**: Servidor FastAPI (Puerto 8000).
3.  **TimescaleDB**: Base de datos de series temporales (Puerto 5432).
4.  **EMQX**: Broker MQTT (Puertos 1883, 8083).
5.  **Redis**: Motor de Tags en tiempo real (Puerto 6379).
6.  **Historian Bridge**: Servicio que guarda datos de MQTT a la base de datos.
7.  **Simulador**: Genera datos de prueba automáticamente (`planta_sim.py`).
8.  **Watchdog**: Monitorea la salud del sistema.

## Instrucciones de Inicio Rápido

Para iniciar todo el sistema con un solo comando:

1.  Abre una terminal en la raíz del proyecto (`scada/SCADA`).
2.  Ejecuta el siguiente comando para construir las imágenes e iniciar los contenedores:

    ```bash
    docker compose up --build -d
    ```

    *El flag `-d` ejecuta los servicios en segundo plano.*

3.  Verifica que los contenedores estén corriendo:

    ```bash
    docker compose ps
    ```

    Deberías ver todos los servicios (frontend, backend, timescaledb, emqx, redis, bridge, watchdog, simulator) con estado "Up".

4.  Si es la primera vez que lo corres, el frontend puede tardar unos minutos en instalar las dependencias (`npm install`). Puedes ver los logs del frontend con:

    ```bash
    docker compose logs -f frontend
    ```

    Espera hasta ver algo como `Local: http://localhost:5173/`.

## Acceso al Sistema

Una vez iniciado:

- **Dashboard (Frontend)**: [http://localhost:5173](http://localhost:5173)
- **API Documentation (Backend)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **EMQX Dashboard**: [http://localhost:18083](http://localhost:18083) (Usuario: `admin`, Password: `public`)

## Desarrollo Local (Opcional)

Si deseas trabajar en el código del frontend o backend sin reiniciar contenedores constantemente:

### Frontend
El contenedor de frontend ya está configurado para reflejar cambios en tiempo real (Hot Reload). Simplemente edita los archivos en la carpeta `frontend/` y verás los cambios en el navegador.

### Backend
Si prefieres correr el backend fuera de Docker:
1.  Detén el contenedor del backend: `docker compose stop backend`.
2.  Crea un entorno virtual: `python -m venv venv`.
3.  Actívalo: `source venv/bin/activate`.
4.  Instala dependencias: `pip install -r requirements.txt`.
5.  Configura las variables de entorno para que apunten a los servicios de Docker (localhost):
    ```bash
    export REDIS_HOST=localhost
    export DB_HOST=localhost
    export MQTT_BROKER=localhost
    ```
6.  Ejecuta el servidor: `uvicorn backend_api:app --reload`.

## Solución de Problemas

- **Conflictos de Puerto**: Si algún puerto (ej. 5432 Postgres, 6379 Redis) ya está en uso en tu PC, deberás detener tus servicios locales o modificar el `docker-compose.yml`.
- **Database Error**: Si el backend falla al conectar a la DB al inicio, es normal; Docker a veces tarda en iniciar la base de datos. El contenedor se reiniciará automáticamente hasta conectar.
- **Permisos**: Si tienes problemas de permisos con volúmenes en Linux, asegúrate de que tu usuario tenga permisos sobre la carpeta del proyecto o usa `sudo` si es estrictamente necesario (aunque no recomendado para desarrollo).
