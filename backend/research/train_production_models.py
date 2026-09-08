"""
Train and serialize production XGBoost models for FloodWatch:
1. Point estimators for +1h, +3h, +6h water level forecast (meters).
2. Dedicated Quantile Regressors (q=0.05 and q=0.95) for statistically grounded 90% empirical intervals.
3. Feature importance and training metadata extraction.
4. Monotonic constraints to guarantee physical validity (water level non-decreasing with respect to rain & saturation).
"""

import os
import json
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "bad_muenstereifel_real_hourly_2021_2023.csv")
MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "services", "ml", "models"))
os.makedirs(MODEL_DIR, exist_ok=True)

print("=" * 80)
print("TRAINING PRODUCTION ML MODELS FOR FLOODWATCH (DEDICATED QUANTILES)")
print("=" * 80)

df = pd.read_csv(DATA_PATH, parse_dates=["time"]).sort_values("time").reset_index(drop=True)

# 1. Feature Engineering
df["soil_moisture_pct"] = ((df["soil_moisture_0_to_7cm"] - 0.08) / (0.45 - 0.08) * 100.0).clip(0, 100)

df["rain_1h"] = df["precipitation"]
df["rain_3h_sum"] = df["precipitation"].rolling(3, min_periods=1).sum()
df["rain_6h_sum"] = df["precipitation"].rolling(6, min_periods=1).sum()
df["rain_12h_sum"] = df["precipitation"].rolling(12, min_periods=1).sum()
df["rain_24h_sum"] = df["precipitation"].rolling(24, min_periods=1).sum()

api_vals = []
c_api = 0.0
for p in df["precipitation"]:
    c_api = p + 0.85 * c_api
    api_vals.append(c_api)
df["api_index"] = api_vals

df["water_level_lag1"] = df["water_level"].shift(1)
df["water_level_lag2"] = df["water_level"].shift(2)
df["water_level_lag3"] = df["water_level"].shift(3)
df["water_rise_rate_1h"] = df["water_level"] - df["water_level_lag1"]
df["water_rise_rate_3h"] = (df["water_level"] - df["water_level_lag3"]) / 3.0

df["hour_sin"] = np.sin(2 * np.pi * df["time"].dt.hour / 24.0)
df["hour_cos"] = np.cos(2 * np.pi * df["time"].dt.hour / 24.0)
df["month_sin"] = np.sin(2 * np.pi * df["time"].dt.month / 12.0)
df["month_cos"] = np.cos(2 * np.pi * df["time"].dt.month / 12.0)

# Targets
df["target_1h"] = df["water_level"].shift(-1)
df["target_3h"] = df["water_level"].shift(-3)
df["target_6h"] = df["water_level"].shift(-6)

clean_df = df.dropna().copy().reset_index(drop=True)
print(f"Dataset ready for training: {len(clean_df)} records")

features = [
    "water_level", "water_level_lag1", "water_level_lag2", "water_level_lag3",
    "water_rise_rate_1h", "water_rise_rate_3h",
    "rain_1h", "rain_3h_sum", "rain_6h_sum", "rain_12h_sum", "rain_24h_sum",
    "api_index", "soil_moisture_pct",
    "temperature_2m", "relative_humidity_2m", "surface_pressure",
    "hour_sin", "hour_cos", "month_sin", "month_cos"
]

# Monotonic constraint tuple: +1 for positive monotonicity on rain and soil moisture
monotone_constraints = tuple(1 if ("rain" in f or "soil" in f or "api" in f) else 0 for f in features)

X = clean_df[features]
metadata = {
    "model_name": "floodwatch_erft_multi_horizon_xgboost",
    "version": "1.0.0",
    "features": features,
    "horizons": [1, 3, 6],
    "metrics": {},
    "feature_importances": {}
}

# Train models for each horizon
for h in [1, 3, 6]:
    target_col = f"target_{h}h"
    y = clean_df[target_col].values
    print(f"\n--- Training Horizon +{h}h Models ---")

    # 1. Point Predictor
    m_point = xgb.XGBRegressor(
        objective="reg:squarederror",
        n_estimators=150,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.1,
        reg_lambda=1.0,
        monotone_constraints=monotone_constraints,
        random_state=42,
        n_jobs=-1
    )
    m_point.fit(X, y)
    point_path = os.path.join(MODEL_DIR, f"xgb_{h}h.json")
    m_point.save_model(point_path)
    print(f"  [OK] Saved point predictor: {point_path}")

    # Evaluate point metrics
    y_pred = m_point.predict(X)
    mae = float(mean_absolute_error(y, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y, y_pred)))
    r2 = float(r2_score(y, y_pred))
    metadata["metrics"][f"{h}h"] = {"mae": mae, "rmse": rmse, "r2": r2}
    print(f"  Training Fit (+{h}h) -> MAE: {mae:.4f}m, RMSE: {rmse:.4f}m, R²: {r2:.4f}")

    # Feature Importance
    importances = m_point.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    fi_dict = {}
    for idx in sorted_idx:
        score = float(importances[idx])
        tier = "High influence" if score > 0.15 else ("Moderate influence" if score > 0.05 else "Low influence")
        fi_dict[features[idx]] = {"importance": score, "tier": tier}
    metadata["feature_importances"][f"{h}h"] = fi_dict

    # 2. Lower Bound (Quantile 0.05)
    m_q05 = xgb.XGBRegressor(
        objective="reg:quantileerror",
        quantile_alpha=0.05,
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        monotone_constraints=monotone_constraints,
        random_state=42,
        n_jobs=-1
    )
    m_q05.fit(X, y)
    q05_path = os.path.join(MODEL_DIR, f"q05_{h}h.json")
    m_q05.save_model(q05_path)
    print(f"  [OK] Saved dedicated 5th percentile model: {q05_path}")

    # 3. Upper Bound (Quantile 0.95)
    m_q95 = xgb.XGBRegressor(
        objective="reg:quantileerror",
        quantile_alpha=0.95,
        n_estimators=100,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        monotone_constraints=monotone_constraints,
        random_state=42,
        n_jobs=-1
    )
    m_q95.fit(X, y)
    q95_path = os.path.join(MODEL_DIR, f"q95_{h}h.json")
    m_q95.save_model(q95_path)
    print(f"  [OK] Saved dedicated 95th percentile model: {q95_path}")

# Save metadata
meta_path = os.path.join(MODEL_DIR, "model_metadata.json")
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(metadata, f, indent=2)
print(f"\n[OK] Metadata saved to: {meta_path}")
print("ALL PRODUCTION ML MODELS SUCCESSFULLY TRAINED AND SERIALIZED!")
