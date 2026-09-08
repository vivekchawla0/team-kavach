from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    dashboard,
    sensors,
    analytics,
    alerts,
    weather,
    risk,
    telemetry,
    simulation,
    reports,
    ml,
    blynk
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(sensors.router, prefix="/sensors", tags=["Sensors"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(weather.router, prefix="/weather", tags=["Weather"])
api_router.include_router(risk.router, prefix="/risk", tags=["Hydrological Risk Engine"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["IoT Telemetry"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
api_router.include_router(blynk.router, prefix="/blynk", tags=["Blynk Cloud Integration"])


