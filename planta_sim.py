import paho.mqtt.client as mqtt
import json
import time
import random
import uuid
import os
from datetime import datetime, timezone
import threading

TAGS = [
    {"path": "planta_central/cocimiento/tanque_01/nivel", "unit": "%", "range": (70, 85)},
    {"path": "planta_central/cocimiento/tanque_01/temperatura", "unit": "°C", "range": (88, 92)},
    {"path": "planta_central/empaquetado/linea_01/motor_principal/corriente", "unit": "A", "range": (12, 15)},
    {"path": "planta_central/empaquetado/linea_01/motor_principal/estado", "unit": "binary", "range": (0, 1)},
    {"path": "planta_central/servicios/caldera/presion", "unit": "bar", "range": (6, 8)},
    {"path": "planta_central/cocimiento/tanque_01/presion", "unit": "bar", "range": (2, 4)},
    {"path": "planta_central/empaquetado/linea_01/velocidad", "unit": "rpm", "range": (1400, 1600)},
    {"path": "planta_central/servicios/caldera/temperatura", "unit": "°C", "range": (150, 180)},
    {"path": "planta_central/servicios/energia/consumo", "unit": "kW", "range": (400, 500)}
]

# State for control: {tag_path: {"mode": "AUTO" | "MANUAL" | "OFF", "value": float}}
TAG_STATE = {}
for tag in TAGS:
    TAG_STATE[tag["path"]] = {"mode": "AUTO", "value": 0}

BROKER = os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", 1883))

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Conectado al Broker con éxito")
        client.subscribe("sim/control")
    else:
        print(f"❌ Error de conexión: {rc}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        path = payload.get("path")
        mode = payload.get("mode") # AUTO, MANUAL, OFF
        value = payload.get("value")
        range_min = payload.get("range_min")
        range_max = payload.get("range_max")

        if path in TAG_STATE:
            if mode:
                TAG_STATE[path]["mode"] = mode
                print(f"🎮 Control: {path} set to {mode}")
            if value is not None:
                TAG_STATE[path]["value"] = float(value)
                print(f"🎮 Control: {path} value set to {value}")
            if range_min is not None and range_max is not None:
                 # Update the global TAGS definition? No, better to keep state in TAG_STATE
                 # But we iterate TAGS. Let's add range overrides to TAG_STATE
                 TAG_STATE[path]["range"] = (float(range_min), float(range_max))
                 print(f"📏 Range: {path} set to ({range_min}, {range_max})")

    except Exception as e:
        print(f"❌ Error processing control message: {e}")

# Generar un ID de cliente único para evitar conflictos
client_id = f"PLANT_SIM_{uuid.uuid4().hex[:6]}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id)
client.on_connect = on_connect
client.on_message = on_message

try:
    print(f"🚀 Iniciando Simulación de Planta [ID: {client_id}] en {BROKER}:{PORT}...")
    client.connect(BROKER, PORT, 60)
    client.loop_start()

    while True:
        for tag in TAGS:
            path = tag["path"]
            state = TAG_STATE.get(path, {"mode": "AUTO", "value": 0})
            
            # Use dynamic range if available, else default
            current_range = state.get("range", tag["range"])
            
            val = 0
            
            if state["mode"] == "OFF":
                val = 0
            elif state["mode"] == "MANUAL":
                val = state["value"]
            else: # AUTO
                if tag["unit"] == "binary":
                    val = 1 # Simple Logic for binary in auto
                else:
                    val = round(random.uniform(current_range[0], current_range[1]), 2)
            
            payload = {
                "v": val,
                "u": tag["unit"],
                "q": 192,
                "t": datetime.now(timezone.utc).isoformat(),
                "mode": state["mode"], # broadcast mode for frontend sync,
                "range": current_range # broadcast range for frontend sync
            }
            
            client.publish(tag["path"], json.dumps(payload), qos=1)
            # print(f"⬆️ {tag['path']} -> {val} {tag['unit']} ({state['mode']})") # Reduced log noise
        
        # print("-" * 30)
        time.sleep(2) # Slightly faster updates

except KeyboardInterrupt:
    print("\n🛑 Simulación detenida.")
    client.loop_stop()
    client.disconnect()
except Exception as e:
    print(f"❌ Error: {e}")
