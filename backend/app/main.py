import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
from app.core.websocket import ws_manager
from app.api.v1.api import api_router
from seed_data import seed_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("floodwatch")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing FloodWatch Monitoring & Warning System...")
    # Verify tables and seed if necessary
    try:
        seed_database()
        logger.info("Database verified and ready.")
    except Exception as e:
        logger.warning(f"Database startup check note: {e}")
    yield
    logger.info("FloodWatch system shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Real-Time Flood Monitoring, Hydrological Telemetry & AI Risk Analysis Platform for Bad Münstereifel",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount REST API
app.include_router(api_router, prefix=settings.API_V1_STR)


# WebSocket Endpoint for Live Telemetry & Alerts
@app.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection open and accept client heartbeats/messages
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket client error: {e}")
        ws_manager.disconnect(websocket)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "FloodWatch Backend",
        "version": settings.VERSION,
        "database": "connected"
    }


# Mount Frontend directory if exists (serves production React build if dist exists)
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
dist_dir = os.path.join(frontend_dir, "dist")
static_dir = dist_dir if os.path.exists(dist_dir) else frontend_dir
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="frontend")

