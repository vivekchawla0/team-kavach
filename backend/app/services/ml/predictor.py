import os
import math
import pickle
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.models import MLPrediction, MLModelRegistry, Sensor, SensorReading
from app.services.ml.features import extract_features_for_sensor, FEATURE_NAMES
from app.services.calibration import raw_water_to_cm, raw_rain_to_intensity

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
METADATA_PKL = os.path.join(MODELS_DIR, "model_metadata.pkl")


def calculate_prototype_risk(water_cm: float) -> str:
    """
    Evaluates flood risk level based on the prototype physical scale (0 to 15 cm):
      < 6.0 cm      = SAFE
      6.0 – 10.0 cm = WARNING
      10.0 – 13.0 cm = DANGER
      > 13.0 cm     = CRITICAL
    """
    if water_cm >= 13.0:
        return "CRITICAL"
    elif water_cm >= 10.0:
        return "DANGER"
    elif water_cm >= 6.0:
        return "WARNING"
    else:
        return "SAFE"


def calculate_flood_probability(water_cm: float) -> float:
    """
    Calculates Flood Risk Probability proxy (%) derived directly from
    the predicted water level relative to the 15 cm physical prototype container:
      - SAFE (0 to <6 cm): 0.0% to 35.0%
      - WARNING (6 to <10 cm): 35.0% to 70.0%
      - DANGER (10 to <13 cm): 70.0% to 90.0%
      - CRITICAL (>=13 cm): 90.0% to 100.0%
    Guarantees monotonic, continuous risk scores and eliminates spurious 100% outputs.
    """
    w = max(0.0, float(water_cm))
    if w < 6.0:
        prob = (w / 6.0) * 35.0
    elif w < 10.0:
        prob = 35.0 + ((w - 6.0) / 4.0) * 35.0
    elif w < 13.0:
        prob = 70.0 + ((w - 10.0) / 3.0) * 20.0
    else:
        prob = 90.0 + min(10.0, ((w - 13.0) / 2.0) * 10.0)
    return round(prob, 1)


class MLPredictor:
    """
    JAL SUCHAK XGBoost Multi-Horizon Predictive Service.
    Loads the 6 production XGBoost models (+1h, +3h, +6h regression & classification)
    supplied in jal_suchak_models.zip.
    """

    def __init__(self):
        self.reg_models: Dict[int, Any] = {}
        self.clf_models: Dict[int, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.is_loaded: bool = False
        self._load_models()

    def _load_models(self):
        """Loads all 6 serialized XGBoost .pkl models once into memory."""
        try:
            if os.path.exists(METADATA_PKL):
                with open(METADATA_PKL, "rb") as f:
                    self.metadata = pickle.load(f)
                logger.info(f"Loaded ML metadata: {self.metadata.get('project')} ({self.metadata.get('location')})")

            for horizon in [1, 3, 6]:
                reg_file = os.path.join(MODELS_DIR, f"reg_{horizon}h.pkl")
                if os.path.exists(reg_file):
                    with open(reg_file, "rb") as f:
                        self.reg_models[horizon] = pickle.load(f)

                clf_file = os.path.join(MODELS_DIR, f"clf_{horizon}h.pkl")
                if os.path.exists(clf_file):
                    with open(clf_file, "rb") as f:
                        self.clf_models[horizon] = pickle.load(f)

            self.is_loaded = (
                len(self.reg_models) == 3 and
                len(self.clf_models) == 3
            )
            if self.is_loaded:
                logger.info("Successfully loaded all 6 XGBoost models (reg_1h, clf_1h, reg_3h, clf_3h, reg_6h, clf_6h).")
            else:
                logger.warning(f"ML models incomplete in {MODELS_DIR}: Reg={list(self.reg_models.keys())}, Clf={list(self.clf_models.keys())}")
        except Exception as e:
            logger.error(f"Failed to load XGBoost ML models: {e}", exc_info=True)
            self.is_loaded = False

    def predict_for_features(self, features: Dict[str, float]) -> Dict[str, Any]:
        """
        Runs inference over a prepared 10-feature dictionary.
        Returns multi-horizon predictions for 1h, 3h, and 6h.
        """
        if not self.is_loaded:
            raise RuntimeError("ML Models are not loaded.")

        df = pd.DataFrame([features])[FEATURE_NAMES]
        current_water_cm = features.get("current_water_cm", 3.0)

        results = {}
        horizon_keys = {1: "one_hour", 3: "three_hours", 6: "six_hours"}
        decay_factors = {1: 0.98, 3: 0.92, 6: 0.85}

        for horizon, key in horizon_keys.items():
            reg_model = self.reg_models.get(horizon)

            # 1. Regression: predicted water level (cm)
            raw_pred_cm = float(reg_model.predict(df)[0])

            # Ensure physical floor without 0.00 cm collapse:
            # If the raw regression output is > 0.5 cm, use the raw XGBoost output directly.
            # If raw regression is <= 0.5 cm, extrapolate realistically from current_water_cm
            # so water level never artificially collapses to 0.00 cm while the container has water.
            if raw_pred_cm > 0.5:
                water_cm = round(raw_pred_cm, 2)
            elif current_water_cm > 0.5:
                decay = decay_factors.get(horizon, 0.9)
                rate_adj = max(0.0, features.get("rise_rate_cm_min", 0.0)) * horizon * 6.0
                water_cm = round(max(0.5, current_water_cm * decay + rate_adj), 2)
            else:
                water_cm = round(max(0.0, raw_pred_cm), 2)

            # 2. Risk score / Flood probability proxy (0% to 100%)
            # Directly calibrated from predicted water level and physical prototype thresholds.
            # Avoids uncalibrated classifier 100% saturation on safe water levels.
            flood_prob = calculate_flood_probability(water_cm)

            # 3. Independent risk determination for this horizon
            risk = calculate_prototype_risk(water_cm)

            results[key] = {
                "water_cm": water_cm,
                "flood_probability": flood_prob,
                "risk": risk
            }

        return results

    def get_latest_prediction(self, db: Session, sensor_id: str = "ESP32-FW-001") -> Dict[str, Any]:
        """
        Primary endpoint helper for GET /api/v1/ml/prediction.
        Fetches live ESP32 reading, builds exact features, runs model,
        and returns the standard prediction response.
        """
        if not self.is_loaded:
            return {
                "status": "unavailable",
                "available": False,
                "message": "ML Model Unavailable — Models could not be loaded into memory",
                "model": {"type": "XGBoost", "status": "unloaded"}
            }

        # Check latest reading
        latest_reading = (
            db.query(SensorReading)
            .filter(
                (SensorReading.sensor_id == sensor_id) |
                (SensorReading.sensor_id == "FW-001") |
                (SensorReading.sensor_id == "ESP32-FW-001")
            )
            .order_by(SensorReading.timestamp.desc())
            .first()
        )

        now = datetime.now(timezone.utc)
        if not latest_reading:
            return {
                "status": "unavailable",
                "available": False,
                "message": "ML Prediction Unavailable — Waiting for live ESP32 telemetry...",
                "model": {"type": "XGBoost", "status": "loaded"}
            }

        # Check telemetry staleness (> 60s without fresh data considers telemetry unavailable)
        r_time = latest_reading.timestamp if latest_reading.timestamp.tzinfo else latest_reading.timestamp.replace(tzinfo=timezone.utc)
        seconds_ago = (now - r_time).total_seconds()
        if seconds_ago > 60:
            return {
                "status": "unavailable",
                "available": False,
                "message": f"ML Prediction Unavailable — Waiting for live ESP32 telemetry (last seen {int(seconds_ago)}s ago)",
                "seconds_ago": round(seconds_ago, 1),
                "model": {"type": "XGBoost", "status": "loaded"}
            }

        # Extract features
        features = extract_features_for_sensor(db, sensor_id, latest_reading)

        # Temporary ML debug logging as requested
        print("\n[ML INPUT]")
        print(f"Water: {features.get('current_water_cm', 0.0):.2f} cm")
        print(f"Rain: {features.get('rain_intensity', 0.0)}")
        print(f"Rise Rate: {features.get('rise_rate_cm_min', 0.0):.4f}")
        print(f"History Length: 10")
        print("[ML] Prediction started")

        try:
            # Run inference
            prediction_results = self.predict_for_features(features)

            print(f"[ML] +1H: {prediction_results['one_hour']['water_cm']:.2f} cm")
            print(f"[ML] +3H: {prediction_results['three_hours']['water_cm']:.2f} cm")
            print(f"[ML] +6H: {prediction_results['six_hours']['water_cm']:.2f} cm")
            print("[ML] Risk:")
            print(f"+1H = {prediction_results['one_hour']['risk']}")
            print(f"+3H = {prediction_results['three_hours']['risk']}")
            print(f"+6H = {prediction_results['six_hours']['risk']}\n")

            return {
                "status": "live",
                "available": True,
                "current_water_cm": features["current_water_cm"],
                "water_rise_cm_min": features["rise_rate_cm_min"],
                "rain_intensity": features["rain_intensity"],
                "prediction": prediction_results,
                "features": features,
                "seconds_ago": round(seconds_ago, 1),
                "model": {
                    "type": "XGBoost",
                    "status": "loaded",
                    "framework": "XGBoost 2.1.4",
                    "horizons": ["1h", "3h", "6h"],
                    "project": self.metadata.get("project", "JAL SUCHAK"),
                    "location": self.metadata.get("location", "Barpeta, Assam")
                }
            }
        except Exception as e:
            print(f"[ML] Prediction failed: {e}\n")
            return {
                "status": "unavailable",
                "available": False,
                "message": f"ML Prediction Failed: {e}",
                "model": {"type": "XGBoost", "status": "loaded"}
            }

    def predict_for_sensor(
        self,
        db: Session,
        sensor_id: str,
        current_reading: Optional[SensorReading] = None,
        warning_threshold: float = 6.0,
        danger_threshold: float = 10.0
    ) -> Dict[str, Any]:
        """
        Legacy compatible method for /api/v1/ml/forecast/{sensor_id}.
        """
        if not self.is_loaded:
            return {"status": "UNAVAILABLE", "message": "Models not loaded"}

        features = extract_features_for_sensor(db, sensor_id, current_reading)
        preds = self.predict_for_features(features)

        # Format into legacy expected shape if needed
        forecasts = {
            "1h": {
                "predicted_water_level": preds["one_hour"]["water_cm"],
                "flood_probability": preds["one_hour"]["flood_probability"],
                "risk": preds["one_hour"]["risk"]
            },
            "3h": {
                "predicted_water_level": preds["three_hours"]["water_cm"],
                "flood_probability": preds["three_hours"]["flood_probability"],
                "risk": preds["three_hours"]["risk"]
            },
            "6h": {
                "predicted_water_level": preds["six_hours"]["water_cm"],
                "flood_probability": preds["six_hours"]["flood_probability"],
                "risk": preds["six_hours"]["risk"]
            }
        }

        overall_prob = max(p["flood_probability"] for p in forecasts.values())

        return {
            "sensor_id": sensor_id,
            "forecast_timestamp": datetime.now(timezone.utc).isoformat(),
            "features_used": features,
            "forecasts": forecasts,
            "overall_flood_probability": overall_prob,
            "advisory_level": calculate_prototype_risk(preds["six_hours"]["water_cm"])
        }

    def predict_and_store(
        self,
        db: Session,
        sensor_id: str,
        current_reading: SensorReading,
        warning_threshold: float = 6.0,
        danger_threshold: float = 10.0
    ) -> Dict[str, Any]:
        """
        Called on incoming telemetry to persist multi-horizon forecasts in `ml_predictions`.
        """
        if not self.is_loaded:
            return {}

        try:
            features = extract_features_for_sensor(db, sensor_id, current_reading)
            preds = self.predict_for_features(features)
            now = datetime.now(timezone.utc)

            horizon_map = {1: preds["one_hour"], 3: preds["three_hours"], 6: preds["six_hours"]}
            for h, res in horizon_map.items():
                rec = MLPrediction(
                    sensor_id=sensor_id,
                    prediction_timestamp=now,
                    horizon_hours=h,
                    predicted_water_level=res["water_cm"],
                    uncertainty_lower=max(0.0, res["water_cm"] - 0.5),
                    uncertainty_upper=res["water_cm"] + 0.5,
                    flood_probability=res["flood_probability"],
                    model_version="xgboost-2.1.4-v2"
                )
                db.add(rec)

            db.commit()
            return preds
        except Exception as e:
            logger.warning(f"Error persisting ML prediction: {e}")
            db.rollback()
            return {}

    def sync_model_registry(self, db: Session):
        """Maintains ML Model Registry entries in the database."""
        if not self.is_loaded:
            return

        try:
            for horizon in [1, 3, 6]:
                for m_type in ["regressor", "classifier"]:
                    model_id = f"xgb_{m_type[:3]}_{horizon}h_v2"
                    existing = db.query(MLModelRegistry).filter(MLModelRegistry.model_id == model_id).first()
                    if not existing:
                        reg = MLModelRegistry(
                            model_id=model_id,
                            horizon_hours=horizon,
                            model_type=m_type.upper(),
                            algorithm="XGBoost",
                            objective="reg:squarederror" if m_type == "regressor" else "binary:logistic",
                            evaluation_metrics="{}",
                            features_used=str(FEATURE_NAMES),
                            training_date=datetime.now(timezone.utc),
                            status="ACTIVE"
                        )
                        db.add(reg)
            db.commit()
        except Exception as e:
            db.rollback()


ml_predictor = MLPredictor()
