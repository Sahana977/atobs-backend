"""Loads the saved model once and turns request inputs into predictions."""
import json
from datetime import datetime
from functools import lru_cache

import joblib
import numpy as np
import pandas as pd

from app.config import BEST_MODEL_PATH, FEATURES, METRICS_PATH, PEAK_WINDOWS

# Typical sensor values per traffic level — used when the caller doesn't send them
TRAFFIC_DEFAULTS = {
    "low":    dict(vehicle_density=20, avg_speed=45, road_occupancy=0.20, traffic_flow=90),
    "medium": dict(vehicle_density=45, avg_speed=36, road_occupancy=0.38, traffic_flow=160),
    "high":   dict(vehicle_density=70, avg_speed=27, road_occupancy=0.56, traffic_flow=190),
    "severe": dict(vehicle_density=95, avg_speed=18, road_occupancy=0.74, traffic_flow=170),
}


def comfort_label(occ: float) -> str:
    if occ < 50:
        return "comfortable"
    if occ < 80:
        return "moderate"
    if occ < 100:
        return "crowded"
    return "overcrowded"


def is_peak(minute_of_day: int) -> int:
    h = minute_of_day // 60
    return int(any(s <= h < e for s, e in PEAK_WINDOWS))


@lru_cache(maxsize=1)
def load() -> dict:
    if not BEST_MODEL_PATH.exists():
        raise FileNotFoundError("No trained model found. Run: python -m app.ml.train")
    return joblib.load(BEST_MODEL_PATH)


def metrics() -> dict:
    return json.loads(METRICS_PATH.read_text()) if METRICS_PATH.exists() else {}


def build_row(trip_id: str, stop_id: str, when: datetime, traffic_level: str = "medium",
              delay_min: float = 0.0, **overrides) -> dict:
    minute = when.hour * 60 + when.minute
    angle = 2 * np.pi * minute / 1440
    row = {
        "trip_id": trip_id, "stop_id": stop_id, "traffic_level": traffic_level,
        "delay_min": delay_min, "time_sin": float(np.sin(angle)),
        "time_cos": float(np.cos(angle)), "is_peak_hour": is_peak(minute),
        **TRAFFIC_DEFAULTS[traffic_level],
    }
    row.update({k: v for k, v in overrides.items() if v is not None})
    return row


def predict_rows(rows: list[dict]) -> list[float]:
    model = load()["model"]
    preds = model.predict(pd.DataFrame(rows)[FEATURES])
    return [round(float(np.clip(p, 0, 150)), 1) for p in preds]
