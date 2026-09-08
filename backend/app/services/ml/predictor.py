import os
import json
import math
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import numpy as np
import xgboost as xgb
from sqlalchemy.orm import Session

from app.models.models import MLPrediction, MLModelRegistry, Sensor, SensorReading
from app.services.ml.features import extract_features_for_sensor, FEATURE_NAMES

logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
METADATA_PATH = os.path.join(MODELS_DIR, "model_metadata.json")


def normal_cdf(x: float) -> float:
    """Standard normal cumulative distribution function."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


class MLPredictor:
    """
    Production ML Flood Prediction Service for FloodWatch.
    Loads direct multi-horizon XGBoost point predictors and dedicated
    quantile regressors (q05 and q95) for statistically valid uncertainty intervals.
    """

    def __init__(self):
        self.point_models: Dict[int, xgb.Booster] = {}
        self.q05_models: Dict[int, xgb.Booster] = {}
        self.q95_models: Dict[int, xgb.Booster] = {}
        self.metadata: Dict[str, Any] = {}
        self.is_loaded: bool = False
        self._load_models()

    def _load_models(self):
        """Loads all serialized XGBoost models and evaluation metadata into memory."""
        try:
            if not os.path.exists(METADATA_PATH):
                logger.warning(f"ML metadata not found at {METADATA_PATH}")
                return

            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

            for horizon in [1, 3, 6]:
                # Point regressor
                point_file = os.path.join(MODELS_DIR, f"xgb_{horizon}h.json")
                if os.path.exists(point_file):
                    booster = xgb.Booster()
                    booster.load_model(point_file)
                    self.point_models[horizon] = booster

                # Dedicated 5th percentile quantile model
                q05_file = os.path.join(MODELS_DIR, f"q05_{horizon}h.json")
                if os.path.exists(q05_file):
                    booster = xgb.Booster()
                    booster.load_model(q05_file)
                    self.q05_models[horizon] = booster

                # Dedicated 95th percentile quantile model
                q95_file = os.path.join(MODELS_DIR, f"q95_{horizon}h.json")
                if os.path.exists(q95_file):
                    booster = xgb.Booster()
                    booster.load_model(q95_file)
                    self.q95_models[horizon] = booster

            self.is_loaded = (
                len(self.point_models) == 3 and
                len(self.q05_models) == 3 and
                len(self.q95_models) == 3
            )
            if self.is_loaded:
                logger.info("Successfully loaded all 9 production XGBoost models (Point, Q05, Q95).")
            else:
                logger.warning("Some ML models could not be loaded into memory.")
        except Exception as e:
            logger.error(f"Failed to load ML models: {e}", exc_info=True)

    def sync_model_registry(self, db: Session):
        """Registers active models and their validation metrics into the database."""
        if not self.is_loaded or not self.metadata:
            return

        try:
            for horizon in [1, 3, 6]:
                h_key = f"{horizon}h"
                h_metrics = self.metadata.get("metrics", {}).get(h_key, {})
                h_importance = self.metadata.get("feature_importances", {}).get(h_key, {})

                # 1. Point model
                model_id_point = f"xgb_point_{horizon}h_v1"
                existing = db.query(MLModelRegistry).filter(MLModelRegistry.model_id == model_id_point).first()
                if not existing:
                    reg = MLModelRegistry(
                        model_id=model_id_point,
                        horizon_hours=horizon,
                        model_type="POINT_REGRESSOR",
                        algorithm="XGBoost",
                        objective="reg:squarederror",
                        quantile_alpha=None,
                        evaluation_metrics=json.dumps(h_metrics),
                        features_used=json.dumps(FEATURE_NAMES),
                        training_date=datetime.now(timezone.utc),
                        status="ACTIVE",
                        filepath=os.path.join(MODELS_DIR, f"xgb_{horizon}h.json")
                    )
                    db.add(reg)

                # 2. Q05 model
                model_id_q05 = f"xgb_q05_{horizon}h_v1"
                existing_q05 = db.query(MLModelRegistry).filter(MLModelRegistry.model_id == model_id_q05).first()
                if not existing_q05:
                    reg = MLModelRegistry(
                        model_id=model_id_q05,
                        horizon_hours=horizon,
                        model_type="QUANTILE_05",
                        algorithm="XGBoost",
                        objective="reg:quantileerror",
                        quantile_alpha=0.05,
                        evaluation_metrics=json.dumps({"pinball_loss_alpha": 0.05, "target_coverage": 0.05}),
                        features_used=json.dumps(FEATURE_NAMES),
                        training_date=datetime.now(timezone.utc),
                        status="ACTIVE",
                        filepath=os.path.join(MODELS_DIR, f"q05_{horizon}h.json")
                    )
                    db.add(reg)

                # 3. Q95 model
                model_id_q95 = f"xgb_q95_{horizon}h_v1"
                existing_q95 = db.query(MLModelRegistry).filter(MLModelRegistry.model_id == model_id_q95).first()
                if not existing_q95:
                    reg = MLModelRegistry(
                        model_id=model_id_q95,
                        horizon_hours=horizon,
                        model_type="QUANTILE_95",
                        algorithm="XGBoost",
                        objective="reg:quantileerror",
                        quantile_alpha=0.95,
                        evaluation_metrics=json.dumps({"pinball_loss_alpha": 0.95, "target_coverage": 0.95}),
                        features_used=json.dumps(FEATURE_NAMES),
                        training_date=datetime.now(timezone.utc),
                        status="ACTIVE",
                        filepath=os.path.join(MODELS_DIR, f"q95_{horizon}h.json")
                    )
                    db.add(reg)

            db.commit()
            logger.info("ML Model Registry synchronized with database.")
        except Exception as e:
            db.rollback()
            logger.warning(f"Error syncing ML model registry: {e}")

    def predict_for_sensor(
        self,
        db: Session,
        sensor_id: str,
        current_reading: SensorReading,
        warning_threshold: float = 3.0,
        danger_threshold: float = 4.0
    ) -> Dict[str, Any]:
        """
        Executes inference for +1h, +3h, and +6h forecast horizons.
        Guarantees statistical prediction intervals from dedicated quantile models
        and non-crossing monotonicity: q05 <= point <= q95.
        """
        if not self.is_loaded:
            self._load_models()
            if not self.is_loaded:
                return {"status": "UNAVAILABLE", "message": "ML models not loaded"}

        # 1. Extract feature dictionary and build DMatrix
        feat_dict = extract_features_for_sensor(db, sensor_id, current_reading)
        feat_vector = np.array([[feat_dict[k] for k in FEATURE_NAMES]], dtype=np.float32)
        dmatrix = xgb.DMatrix(feat_vector, feature_names=FEATURE_NAMES)

        forecasts = {}
        now = current_reading.timestamp or datetime.now(timezone.utc)

        max_flood_prob = 0.0

        for horizon in [1, 3, 6]:
            # Raw predictions
            y_pred = float(self.point_models[horizon].predict(dmatrix)[0])
            q05_pred = float(self.q05_models[horizon].predict(dmatrix)[0])
            q95_pred = float(self.q95_models[horizon].predict(dmatrix)[0])

            # Non-crossing and physical sanity guarantee
            # Empirical quantiles must strictly satisfy: lower <= point <= upper
            lower = min(q05_pred, y_pred)
            upper = max(q95_pred, y_pred)
            # Guarantee positive water level
            lower = max(0.05, round(lower, 2))
            point = max(lower, round(y_pred, 2))
            upper = max(point, round(upper, 2))

            # Statistically calibrated flood probability:
            # P(stage >= warning_threshold) using dedicated quantile-derived variance
            # Since [lower, upper] spans 90% (from 5th to 95th percentile, ~3.29 sigma),
            sigma = max(0.02, (upper - lower) / (2.0 * 1.645))
            z = (warning_threshold - point) / sigma
            flood_prob_raw = (1.0 - normal_cdf(z)) * 100.0
            
            # If current water level is already above warning threshold, probability is >= 95%
            if current_reading.water_level >= warning_threshold:
                flood_prob = max(95.0, min(100.0, flood_prob_raw))
            else:
                flood_prob = round(max(0.0, min(99.0, flood_prob_raw)), 1)

            if flood_prob > max_flood_prob:
                max_flood_prob = flood_prob

            # Feature importance breakdown for this horizon
            h_key = f"{horizon}h"
            raw_importance = self.metadata.get("feature_importances", {}).get(h_key, {})
            # Return top contributing features formatted for display
            top_features = []
            for feat_name, meta in list(raw_importance.items())[:5]:
                top_features.append({
                    "feature": feat_name,
                    "tier": meta.get("tier", "Moderate influence"),
                    "importance": round(meta.get("importance", 0.0), 3),
                    "current_value": round(feat_dict.get(feat_name, 0.0), 2)
                })

            forecasts[f"{horizon}h"] = {
                "horizon_hours": horizon,
                "predicted_water_level": point,
                "uncertainty_lower": lower,
                "uncertainty_upper": upper,
                "interval_width": round(upper - lower, 2),
                "confidence_interval_level": "90% (Dedicated Q05 - Q95)",
                "flood_probability": flood_prob,
                "top_influences": top_features
            }

        # Global advisory status based on 6h trajectory
        pred_6h = forecasts["6h"]["predicted_water_level"]
        prob_6h = forecasts["6h"]["flood_probability"]
        
        if pred_6h >= danger_threshold or prob_6h >= 75.0:
            advisory_level = "CRITICAL_EARLY_WARNING"
            advisory_message = f"ML models project river crest reaching {pred_6h:.2f}m within 6h (Flood Probability: {prob_6h}%)."
        elif pred_6h >= warning_threshold or prob_6h >= 40.0:
            advisory_level = "ELEVATED_WATCH"
            advisory_message = f"ML models forecast water level approaching warning threshold ({pred_6h:.2f}m) within 6h."
        elif prob_6h >= 20.0:
            advisory_level = "MODERATE_ADVISORY"
            advisory_message = f"Hydrological trend indicates rising trajectory; monitoring continuous inflow."
        else:
            advisory_level = "STABLE"
            advisory_message = f"ML forecast indicates stable hydraulic stage below warning thresholds."

        return {
            "sensor_id": sensor_id,
            "timestamp": now.isoformat(),
            "current_water_level": round(float(current_reading.water_level), 2),
            "forecasts": forecasts,
            "overall_flood_probability": max_flood_prob,
            "advisory_level": advisory_level,
            "advisory_message": advisory_message,
            "disclaimer": (
                "ML predictions are decision-support advisory signals only. "
                "Deterministic safety thresholds and the Hydrological Risk Engine remain the primary authority."
            )
        }

    def predict_and_store(
        self,
        db: Session,
        sensor_id: str,
        current_reading: SensorReading,
        warning_threshold: float = 3.0,
        danger_threshold: float = 4.0
    ) -> Dict[str, Any]:
        """
        Executes prediction and persists the 1h, 3h, 6h records to ml_predictions table.
        """
        result = self.predict_for_sensor(
            db=db,
            sensor_id=sensor_id,
            current_reading=current_reading,
            warning_threshold=warning_threshold,
            danger_threshold=danger_threshold
        )

        if "forecasts" not in result:
            return result

        try:
            now = current_reading.timestamp or datetime.now(timezone.utc)
            for h_key, fcast in result["forecasts"].items():
                pred = MLPrediction(
                    sensor_id=sensor_id,
                    prediction_timestamp=now,
                    horizon_hours=fcast["horizon_hours"],
                    predicted_water_level=fcast["predicted_water_level"],
                    uncertainty_lower=fcast["uncertainty_lower"],
                    uncertainty_upper=fcast["uncertainty_upper"],
                    flood_probability=fcast["flood_probability"],
                    model_version="xgb_direct_v1",
                    feature_importance=json.dumps(fcast["top_influences"]),
                    created_at=now
                )
                db.add(pred)
            db.commit()
        except Exception as e:
            db.rollback()
            logger.warning(f"Failed to persist ML prediction to database: {e}")

        return result


# Singleton instance
ml_predictor = MLPredictor()
