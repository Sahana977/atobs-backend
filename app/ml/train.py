"""
Train Random Forest / XGBoost / CatBoost, score on 6 metrics, save the best.

Run:  python -m app.ml.train
"""
import json
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (explained_variance_score, mean_absolute_error,
                             mean_absolute_percentage_error, mean_squared_error,
                             median_absolute_error, r2_score)
from sklearn.model_selection import train_test_split

from app.config import BEST_MODEL_PATH, METRICS_PATH, RANDOM_SEED, RAW_CSV, TEST_SIZE
from app.ml import data_gen
from app.ml.models import REGISTRY
from app.ml.preprocess import clean, split_xy


def evaluate(y_true, y_pred) -> dict:
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    nz = y_true > 1  # skip near-zero targets so MAPE doesn't explode
    return {
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "R2": float(r2_score(y_true, y_pred)),
        "MAPE_pct": float(mean_absolute_percentage_error(y_true[nz], y_pred[nz]) * 100),
        "MedAE": float(median_absolute_error(y_true, y_pred)),
        "EVS": float(explained_variance_score(y_true, y_pred)),
    }


def load_data() -> pd.DataFrame:
    if not RAW_CSV.exists():
        print("No dataset found — generating synthetic BMTC-style data.")
        data_gen.generate().to_csv(RAW_CSV, index=False)
    return pd.read_csv(RAW_CSV)


def main():
    raw = load_data()
    df = clean(raw)
    print(f"Rows: {len(raw):,} raw -> {len(df):,} after cleaning\n")

    X, y = split_xy(df)
    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_SEED)

    results, fitted = {}, {}
    for name, build in REGISTRY.items():
        try:
            model = build()
        except ImportError:
            print(f"  [skip] {name}: library not installed")
            continue
        t0 = time.time()
        model.fit(X_tr, y_tr)
        m = evaluate(y_te, model.predict(X_te))
        m["train_seconds"] = round(time.time() - t0, 2)
        results[name], fitted[name] = m, model
        print(f"  {name:<13}" + "  ".join(f"{k}={v:.3f}" for k, v in m.items()))

    if not fitted:
        raise SystemExit("No models trained. Run: pip install -r requirements.txt")

    best = min(results, key=lambda n: results[n]["RMSE"])
    joblib.dump({"name": best, "model": fitted[best]}, BEST_MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(
        {"best_model": best, "rows_train": len(X_tr), "rows_test": len(X_te),
         "results": results}, indent=2))
    print(f"\nBest model: {best} -> {BEST_MODEL_PATH}")


if __name__ == "__main__":
    main()
