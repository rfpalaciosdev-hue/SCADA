TAGS = [
"planta_central/cocimiento/tanque_01/nivel",
"planta_central/cocimiento/tanque_01/temperatura",
"planta_central/empaquetado/linea_01/motor_principal/corriente",
"planta_central/empaquetado/linea_01/motor_principal/estado",
"planta_central/servicios/caldera/presion",
"planta_central/cocimiento/tanque_01/presion",
"planta_central/empaquetado/linea_01/velocidad",
"planta_central/servicios/caldera/temperatura",
"planta_central/servicios/energia/consumo"
]

TAG_ALIASES = {
    "tanque 1": "planta_central/cocimiento/tanque_01",
    "tanque_1": "planta_central/cocimiento/tanque_01",
    "tanque01": "planta_central/cocimiento/tanque_01",

    "caldera": "planta_central/servicios/caldera",
    "horno": "planta_central/servicios/caldera",  # 👈 ejemplo

    "linea 1": "planta_central/empaquetado/linea_01",
    "línea 1": "planta_central/empaquetado/linea_01",
}

SENSOR_ALIASES = {
    "temperatura": "temperatura",
    "presion": "presion",
    "presión": "presion",
    "nivel": "nivel",
    "corriente": "corriente",
    "velocidad": "velocidad",
    "consumo": "consumo",
    "estado": "estado"
}

def resolve_tag(text):
    text = text.lower()
    base = None
    sensor = None

    for k, v in TAG_ALIASES.items():
        if k in text:
            base = v

    for k, v in SENSOR_ALIASES.items():
        if k in text:
            sensor = v

    # 👇 DEFAULT SENSOR (MAGIA)
    if base and not sensor:
        sensor = "temperatura"  # default industrial realista

    if base and sensor:
        tag = f"{base}/{sensor}"
        if tag in TAGS:
            return tag

    return None

def detect_stat(text):
    t = text.lower()
    if "promedio" in t or "media" in t:
        return "avg"
    if "max" in t or "máx" in t:
        return "max"
    if "min" in t or "mín" in t:
        return "min"
    return "last"

def is_conceptual_question(text):
    t = text.lower()
    keywords = [
        "qué pasa si", "que pasa si", "por qué", "porque",
        "como funciona", "cómo funciona", "riesgo",
        "explicame", "explica", "que es", "peligroso",
        "seguridad", "explota", "explosión"
    ]
    return any(k in t for k in keywords)