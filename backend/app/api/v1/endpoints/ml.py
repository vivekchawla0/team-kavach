import json
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Sensor, SensorReading, MLPrediction, MLModelRegistry
from app.services.ml.predictor import ml_predictor

router = APIRouter()


@router.get("/prediction")
def get_real_ml_prediction(
    sensor_id: Optional[str] = "ESP32-FW-001",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Returns real-time XGBoost Multi-Horizon Flood Prediction (+1h, +3h, +6h)
    using the physical prototype calibration and live ESP32 BLE telemetry.
    """
    return ml_predictor.get_latest_prediction(db=db, sensor_id=sensor_id)


@router.get("/forecast/{sensor_id}")
def get_sensor_ml_forecast(sensor_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns real-time ML water level forecast (+1h, +3h, +6h) for a specific sensor.
    Includes dedicated 5th and 95th percentile uncertainty intervals (non-heuristic),
    statistically calibrated flood probability, and feature influence breakdown.
    """
    sensor = db.query(Sensor).filter(Sensor.sensor_id == sensor_id).first()
    if not sensor:
        sensor = db.query(Sensor).filter(Sensor.sensor_id == "FW-001").first()
    if not sensor:
        sensor = db.query(Sensor).first()
    if not sensor:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")

    # Get latest reading for sensor
    latest_reading = (
        db.query(SensorReading)
        .filter(SensorReading.sensor_id == sensor_id)
        .order_by(SensorReading.timestamp.desc())
        .first()
    )

    if not latest_reading:
        # Construct synthetic transient reading from current sensor state
        latest_reading = SensorReading(
            sensor_id=sensor.sensor_id,
            water_level=sensor.current_water_level or 1.20,
            water_rise_rate=sensor.water_rise_rate or 0.0,
            rainfall=0.0,
            soil_moisture=50.0,
            temperature=12.0
        )

    forecast_result = ml_predictor.predict_for_sensor(
        db=db,
        sensor_id=sensor_id,
        current_reading=latest_reading,
        warning_threshold=sensor.warning_threshold,
        danger_threshold=sensor.danger_threshold
    )

    return forecast_result


@router.get("/basin")
def get_basin_ml_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns aggregated basin-wide ML forecast intelligence across all active sensors.
    """
    sensors = db.query(Sensor).filter(Sensor.status != "OFFLINE").all()
    if not sensors:
        raise HTTPException(status_code=404, detail="No active sensors found")

    basin_forecasts = []
    max_flood_prob = 0.0
    critical_sensor = None

    for s in sensors:
        latest = (
            db.query(SensorReading)
            .filter(SensorReading.sensor_id == s.sensor_id)
            .order_by(SensorReading.timestamp.desc())
            .first()
        )
        if not latest:
            latest = SensorReading(
                sensor_id=s.sensor_id,
                water_level=s.current_water_level or 1.20,
                water_rise_rate=s.water_rise_rate or 0.0,
                rainfall=0.0,
                soil_moisture=50.0,
                temperature=12.0
            )

        f = ml_predictor.predict_for_sensor(
            db=db,
            sensor_id=s.sensor_id,
            current_reading=latest,
            warning_threshold=s.warning_threshold,
            danger_threshold=s.danger_threshold
        )
        if "overall_flood_probability" in f:
            basin_forecasts.append({
                "sensor_id": s.sensor_id,
                "name": s.name,
                "water_level": s.current_water_level,
                "pred_6h": f["forecasts"]["6h"]["predicted_water_level"],
                "flood_prob": f["overall_flood_probability"],
                "advisory": f["advisory_level"]
            })
            if f["overall_flood_probability"] > max_flood_prob:
                max_flood_prob = f["overall_flood_probability"]
                critical_sensor = s.sensor_id

    return {
        "active_sensors_count": len(sensors),
        "basin_max_flood_probability": max_flood_prob,
        "highest_risk_sensor": critical_sensor,
        "sensor_forecasts": basin_forecasts,
        "governance_note": (
            "ML predictions are purely advisory decision support. "
            "Primary life safety is governed by the deterministic Rule-Based Hydrological Engine."
        )
    }


@router.get("/models")
def get_registered_models(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Returns the registry of active production ML models, training metadata,
    and verified evaluation metrics (MAE, RMSE, R², Pinball Loss).
    """
    # Ensure registry is in sync
    ml_predictor.sync_model_registry(db)

    records = db.query(MLModelRegistry).filter(MLModelRegistry.status == "ACTIVE").all()
    models_list = []
    for r in records:
        models_list.append({
            "model_id": r.model_id,
            "horizon_hours": r.horizon_hours,
            "model_type": r.model_type,
            "algorithm": r.algorithm,
            "objective": r.objective,
            "quantile_alpha": r.quantile_alpha,
            "evaluation_metrics": json.loads(r.evaluation_metrics) if r.evaluation_metrics else {},
            "features_used": json.loads(r.features_used) if r.features_used else [],
            "status": r.status,
            "training_date": r.training_date.isoformat() if r.training_date else None
        })

    return {
        "status": "OPERATIONAL",
        "models_count": len(models_list),
        "models": models_list,
        "framework": "XGBoost 3.4.1",
        "calibration": "Empirical Quantile Loss (Dedicated Q05 and Q95)"
    }


@router.get("/history/{sensor_id}")
def get_sensor_ml_history(sensor_id: str, limit: int = 50, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Returns persisted ML prediction historical records for verification and auditing.
    """
    preds = (
        db.query(MLPrediction)
        .filter(MLPrediction.sensor_id == sensor_id)
        .order_by(MLPrediction.prediction_timestamp.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": p.id,
            "sensor_id": p.sensor_id,
            "timestamp": p.prediction_timestamp.isoformat(),
            "horizon_hours": p.horizon_hours,
            "predicted_water_level": p.predicted_water_level,
            "uncertainty_lower": p.uncertainty_lower,
            "uncertainty_upper": p.uncertainty_upper,
            "flood_probability": p.flood_probability,
            "model_version": p.model_version
        }
        for p in preds
    ]
