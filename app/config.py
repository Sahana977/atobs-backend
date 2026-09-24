"""Central settings for the ATOBS backend."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MODEL_DIR = ROOT / "models"
DATA_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

RAW_CSV = DATA_DIR / "bmtc_raw.csv"
BEST_MODEL_PATH = MODEL_DIR / "best_model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"
DB_PATH = Path(os.environ.get("ATOBS_DB_PATH", DATA_DIR / "atobs.db"))

# Auth
TOKEN_TTL_HOURS = 24
PASSWORD_ITERATIONS = 100_000

RANDOM_SEED = 42
TEST_SIZE = 0.20

# Peak windows (hours, 24h clock) used for the is_peak_hour flag
PEAK_WINDOWS = [(8, 11), (17, 20)]

# Features the occupancy model consumes (deck slide 10 + traffic features from slide 8)
CATEGORICAL_FEATURES = ["trip_id", "stop_id", "traffic_level"]
NUMERIC_FEATURES = [
    "delay_min", "time_sin", "time_cos", "is_peak_hour",
    "vehicle_density", "avg_speed", "road_occupancy", "traffic_flow",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
TARGET = "occupancy_pct"

# Hyperparameters exactly as in the deck (slide 11)
XGB_PARAMS = dict(n_estimators=100, learning_rate=0.1, random_state=RANDOM_SEED)
CATBOOST_PARAMS = dict(iterations=342, learning_rate=0.13, depth=10,
                       l2_leaf_reg=6.84, random_seed=RANDOM_SEED, verbose=0)
RF_PARAMS = dict(n_estimators=100, random_state=RANDOM_SEED, n_jobs=-1)

# Comfort-aware route cost:  alpha * travel_minutes + beta * crowding_penalty
ROUTE_ALPHA = 1.0
ROUTE_BETA = 0.15
