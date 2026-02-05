import redis
import json
import time
import os
from datetime import datetime, timezone

# Configuración de Redis
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": 0,
    "decode_responses": True
}

r = redis.Redis(**REDIS_CONFIG)

STALE_TIMEOUT_SECONDS = 10

def watchdog_loop():
    print(f"🕵️ Watchdog Service iniciado (Timeout: {STALE_TIMEOUT_SECONDS}s)")
    while True:
        try:
            # Escanear todos los tags actuales
            keys = r.keys("tag_current:*")
            now = datetime.now(timezone.utc)
            
            for key in keys:
                tag_data_raw = r.get(key)
                if not tag_data_raw: continue
                
                tag_data = json.loads(tag_data_raw)
                
                # Si ya tiene mala calidad, ignoramos
                if tag_data.get("q") == 0: continue
                
                # Parsear el timestamp del tag
                try:
                    tag_time = datetime.fromisoformat(tag_data["t"])
                    # Asegurar que comparamos offset-aware
                    if tag_time.tzinfo is None:
                        tag_time = tag_time.replace(tzinfo=timezone.utc)
                except:
                    continue

                # Calcular antigüedad
                age = (now - tag_time).total_seconds()
                
                if age > STALE_TIMEOUT_SECONDS:
                    topic = key.replace("tag_current:", "")
                    print(f"⚠️ TAG STALE DETECTADO: {topic} (Edad: {age:.1f}s). Marcando Calidad MALA.")
                    
                    # Actualizar a Calidad Mala (0)
                    tag_data["q"] = 0
                    r.set(key, json.dumps(tag_data))
                    
                    # Notificar al Front vía WebSocket
                    r.publish("live_updates", json.dumps({
                        "topic": topic, 
                        "val": tag_data["v"], 
                        "ts": tag_data["t"],
                        "q": 0 # Informamos la mala calidad
                    }))
                    
        except Exception as e:
            print(f"❌ Error en Watchdog: {e}")
            
        time.sleep(2) # Ejecutar cada 2 segundos

if __name__ == "__main__":
    watchdog_loop()
