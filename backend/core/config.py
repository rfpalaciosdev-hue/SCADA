import redis
import os
import psycopg2

# ── Redis ──────────────────────────────────────────────────────────────────────
REDIS_CONFIG = {
    "host": os.getenv("REDIS_HOST", "localhost"),
    "port": int(os.getenv("REDIS_PORT", 6379)),
    "db": 0,
    "decode_responses": True,
}

r = redis.Redis(**REDIS_CONFIG)

# ── TimescaleDB ────────────────────────────────────────────────────────────────
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "user": os.getenv("DB_USER", "scada_user"),
    "password": os.getenv("DB_PASS", "scada_admin"),
    "dbname": os.getenv("DB_NAME", "scada_db"),
}


def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)
