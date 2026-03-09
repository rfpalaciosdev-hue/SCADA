from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import alarms_router, chat_router, history_router, sensors_router, tags_router, websocket_routes

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
app.include_router(chat_router.router)
app.include_router(sensors_router.router)
app.include_router(history_router.router)
app.include_router(alarms_router.router)
app.include_router(tags_router.router)
app.include_router(websocket_routes.router)


@app.get("/")
async def root():
    return {"message": "SCADA Backend is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
