import paho.mqtt.client as mqtt
import json
import time
import random
import uuid
import os
from datetime import datetime, timezone

TAGS = [
    {"path": "planta_central/cocimiento/tanque_01/nivel", "unit": "%", "range": (70, 85)},
    {"path": "planta_central/cocimiento/tanque_01/temperatura", "unit": "°C", "range": (88, 92)},
    {"path": "planta_central/empaquetado/linea_01/motor_principal/corriente", "unit": "A", "range": (12, 15)},
    {"path": "planta_central/empaquetado/linea_01/motor_principal/estado", "unit": "binary", "range": (0, 1)},
    {"path": "planta_central/servicios/caldera/presion", "unit": "bar", "range": (6, 8)}
]

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Conectado al Broker con éxito")
    else:
        print(f"❌ Error de conexión: {rc}")

# Generar un ID de cliente único para evitar conflictos
client_id = f"PLANT_SIM_{uuid.uuid4().hex[:6]}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.on_connect = on_connect

try:
    print(f"🚀 Iniciando Simulación de Planta [ID: {client_id}] en {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    while True:
        for tag in TAGS:
            if tag["unit"] == "binary":
                val = 1
            else:
                val = round(random.uniform(tag["range"][0], tag["range"][1]), 2)
            
            payload = {
                "v": val,
                "u": tag["unit"],
                "q": 192,
                "t": datetime.now(timezone.utc).isoformat()
            }
            
            client.publish(tag["path"], json.dumps(payload), qos=1)
            print(f"⬆️ {tag['path']} -> {val} {tag['unit']}")
        
        print("-" * 30)
        time.sleep(3)

except KeyboardInterrupt:
    print("\n🛑 Simulación detenida.")
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"❌ Error: {e}")
