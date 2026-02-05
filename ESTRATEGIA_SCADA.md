# Estrategia de Desarrollo: SCADA Professional (Estilo Ignition)

Este documento detalla la proyección técnica y arquitectónica para la creación de una plataforma de automatización industrial moderna, inspirada en la potencia de **Ignition (Inductive Automation)**, pero optimizada con tecnologías web de última generación.

## 1. Visión General
El objetivo es transformar los datos crudos de la planta en información accionable, utilizando un motor de "Tags" unificado que sirva como única fuente de verdad para toda la empresa.

---

## 2. Arquitectura de Conectividad (MQTT en Detalle)

Hemos seleccionado **MQTT** como el sistema nervioso del proyecto por su eficiencia y capacidad de respuesta. El flujo de datos se divide en 4 etapas:

### Etapa A: Emisión (Planta)
Los PLCs o Gateways actúan como **Publishers**.
*   **Report by Exception (RBE)**: Solo se envía información cuando el valor cambia, ahorrando ancho de banda y procesamiento.
*   **Sparkplug B**: Implementaremos este estándar industrial para lograr "Plug & Play". Los equipos se autodescubren en el dashboard sin configuración manual.

### Etapa B: Tráfico (MQTT Broker)
Un intermediario central (como Mosquitto o EMQX) que desacopla la planta del dashboard.
*   La planta publica datos sin saber quién los lee, asegurando que si el dashboard falla o se actualiza, la operación de la planta **nunca se vea afectada**.

### Etapa C: Inteligencia (Ingestion Engine)
Nuestro backend actúa como un suscriptor inteligente que realiza:
1.  **Normalización**: Traduce distintos formatos de equipos a un estándar único de "Tag".
2.  **Calidad del Dato (Quality Stamps)**: Detecta pérdidas de conexión en milisegundos usando *Last Will and Testament*.
3.  **Contextualización**: Cruza el dato técnico (p. ej., 80°C) con el dato de negocio (p. ej., "Hormada Lote #405").

### Etapa D: Visualización (Perspective Style)
Interfaz web-based que no solo muestra gráficos, sino que permite interactuar.
*   **Tag Binding**: Las propiedades visuales (colores, niveles) se "atan" directamente a las rutas de los tags.
*   **Mobile-Responsive**: Acceso desde cualquier dispositivo (Celular, Tablet, HMI).

---

## 3. Conceptos Core "Estilo Ignition"

Para alcanzar el nivel de Ignition, el sistema se basará en:

*   **Tag Engine**: Un sistema jerárquico (`Sucursal/Linea/Equipo/Sensor`) que mantiene el estado actual de toda la planta en memoria (latencia ultra-baja).
*   **UDTs (user Defined Types)**: Plantillas para equipos. Definiendo una vez cómo es un "Motor Standard", podemos crear cientos de instancias idénticas instantáneamente.
*   **Historian Automático**: Archivo de datos históricos inteligente en bases de datos de series temporales (TimescaleDB).
*   **Alarm Engine**: Monitoreo constante de umbrales con sistema de reconocimiento (Acknowledge) y notificaciones externas.

---

## 4. Agregados y Diferenciadores (Plus)

A diferencia de un SCADA tradicional, este proyecto proyecta:
*   **IA de Análisis**: Chatbot integrado que puede responder preguntas sobre el historial de producción analizando los datos por nosotros.
*   **Modo Colaborativo**: Visualización de múltiples operarios viendo la misma pantalla en tiempo real.
*   **Security by Design**: Autenticación moderna, logs de auditoría (quién hizo qué) y cifrado de punta a punta.

---

## 5. Persistencia y Manejo de Datos (El Historian)

Para gestionar cientos de lecturas por minuto sin degradar el rendimiento, el sistema implementará una arquitectura de **Series Temporales (Time-Series)**:

### A. Base de Datos: TimescaleDB
Utilizaremos **TimescaleDB** (basado en PostgreSQL) por su capacidad de manejar billones de filas mediante:
*   **Hypertables**: División automática de datos en bloques de tiempo (chunks), acelerando las consultas históricas.
*   **Compresión Nativa**: Ahorro de hasta el 90% de espacio en disco en datos antiguos.

### B. Optimización de Ingesta (Historian Efficiency)
Para evitar la saturación del sistema, aplicaremos tres técnicas clave:
1.  **Deadband (Banda Muerta)**: Solo se guarda el dato si el cambio respecto a la última lectura supera un umbral definido. Esto elimina "ruido" y ahorra espacio.
2.  **Batching**: Los registros no se escriben uno a uno; se agrupan en memoria y se inyectan en la DB por lotes cada pocos milisegundos.
3.  **Downsampling**: Proceso opcional para reducir la resolución de datos muy antiguos (ej. promediar minutos por horas después de un año) para mantener el sistema ágil perpetuamente.

---

## 6. Hoja de Ruta (Roadmap)
1.  **Módulo de Infraestructura**: Configuración de Docker con TimescaleDB y MQTT Broker persistente.
2.  **Módulo de Tags & Ingesta**: Crear el "Bridge" que recibe MQTT, aplica Deadband y guarda en el Historian.
3.  **Módulo de Visualización (Perspective)**: Dashboards con capacidad de consultar tendencias históricas instantáneas.
