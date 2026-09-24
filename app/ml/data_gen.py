"""
Synthetic BMTC-style dataset generator.

Swap in the real BMTC export whenever you have it: keep the same column
names and drop the file at data/bmtc_raw.csv — training picks it up automatically.
"""
import numpy as np
import pandas as pd

from app.config import PEAK_WINDOWS, RANDOM_SEED, RAW_CSV

TRAFFIC_LEVELS = ["low", "medium", "high", "severe"]
TRIP_IDS = [f"T{i:03d}" for i in range(1, 61)]
STOP_IDS = [f"S{i:02d}" for i in range(1, 25)]  # 24 stops = 24 graph nodes


def _is_peak(hour: np.ndarray) -> np.ndarray:
    flag = np.zeros_like(hour, dtype=int)
    for start, end in PEAK_WINDOWS:
        flag |= ((hour >= start) & (hour < end)).astype(int)
    return flag


def generate(n_rows: int = 48_120, seed: int = RANDOM_SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    minute_of_day = rng.integers(5 * 60, 23 * 60, n_rows)
    peak = _is_peak(minute_of_day // 60)

    traffic_level = np.where(
        peak == 1,
        rng.choice(TRAFFIC_LEVELS, n_rows, p=[0.05, 0.25, 0.45, 0.25]),
        rng.choice(TRAFFIC_LEVELS, n_rows, p=[0.40, 0.35, 0.20, 0.05]),
    )
    lvl = pd.Series(traffic_level).map({l: i for i, l in enumerate(TRAFFIC_LEVELS)}).to_numpy()

    vehicle_density = np.clip(20 + lvl * 25 + rng.normal(0, 8, n_rows), 5, None)
    avg_speed = np.clip(45 - lvl * 9 + rng.normal(0, 4, n_rows), 4, 60)
    road_occupancy = np.clip(0.2 + lvl * 0.18 + rng.normal(0, 0.05, n_rows), 0.05, 1.0)
    traffic_flow = np.clip(vehicle_density * avg_speed / 10 + rng.normal(0, 15, n_rows), 10, None)
    delay_min = np.clip(lvl * 3 + rng.gamma(1.5, 1.2, n_rows), 0, 45)

    trip = rng.choice(TRIP_IDS, n_rows)
    stop = rng.choice(STOP_IDS, n_rows)
    stop_num = pd.Series(stop).str[1:].astype(int).to_numpy()
    trip_bias = pd.Series(trip).str[1:].astype(int).to_numpy() % 7

    # Ground-truth occupancy, % of capacity (can exceed 100 when overcrowded)
    occupancy = (
        35 + 22 * peak + 6 * lvl + 0.9 * delay_min
        + 10 * np.sin(np.pi * stop_num / 24) + 1.5 * trip_bias
        + rng.normal(0, 8, n_rows)
    )

    df = pd.DataFrame({
        "trip_id": trip,
        "stop_id": stop,
        "minute_of_day": minute_of_day,
        "is_peak_hour": peak,
        "traffic_level": traffic_level,
        "vehicle_density": vehicle_density.round(2),
        "avg_speed": avg_speed.round(2),
        "road_occupancy": road_occupancy.round(3),
        "traffic_flow": traffic_flow.round(2),
        "delay_min": delay_min.round(2),
        "occupancy_pct": np.clip(occupancy, 0, 150).round(1),
    })

    # ~1.8% missing values so the cleaning step has real work (48,120 -> ~47,270)
    df.loc[rng.random(n_rows) < 0.018, "avg_speed"] = np.nan
    return df


if __name__ == "__main__":
    data = generate()
    data.to_csv(RAW_CSV, index=False)
    print(f"Wrote {len(data):,} rows -> {RAW_CSV}")
