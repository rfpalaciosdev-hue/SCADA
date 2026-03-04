from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import alarms, chat, history, sensors, tags, websocket

app = FastAPI(title="SCADA Real-Time API")

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción poner la URL del front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(sensors.router)
app.include_router(history.router)
app.include_router(alarms.router)
app.include_router(tags.router)
app.include_router(websocket.router)


@app.get("/")
async def root():
    return {"message": "SCADA Backend is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
