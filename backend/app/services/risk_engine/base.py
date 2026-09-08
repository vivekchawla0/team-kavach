from typing import Protocol, Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel


class RiskAssessmentOutput(BaseModel):
    sensor_id: Optional[str] = None
    overall_score: float              # 0.0 to 100.0
    overall_level: str                # LOW, MODERATE, HIGH, CRITICAL
    status_label: str
    status_description: str
    factors: Dict[str, Dict[str, Any]]
    assessed_at: datetime


class RiskEngine(Protocol):
    """
    Abstract Protocol defining the contract for any Flood Risk Engine.
    Both RuleBasedRiskEngine and FutureMLRiskEngine implement this exact interface.
    """
    def calculate_sensor_risk(
        self,
        water_level: float,
        water_rise_rate: float,
        rainfall: float,
        soil_moisture: float,
        warning_threshold: float,
        danger_threshold: float,
        forecast_rain_mm: float = 0.0,
        sensor_id: Optional[str] = None
    ) -> RiskAssessmentOutput:
        ...

    def calculate_basin_risk(
        self,
        avg_water_level: float,
        max_water_level: float,
        avg_rise_rate: float,
        current_rainfall: float,
        soil_moisture: float,
        forecast_24h_rainfall: float
    ) -> RiskAssessmentOutput:
        ...
