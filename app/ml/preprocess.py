"""Cleaning + feature engineering (deck slide 8)."""
import numpy as np
import pandas as pd

from app.config import CATEGORICAL_FEATURES, FEATURES, RANDOM_SEED, TARGET


def add_cyclic_time(df: pd.DataFrame) -> pd.DataFrame:
    """Encode minute-of-day on a circle so 23:59 and 00:01 are neighbours."""
    angle = 2 * np.pi * df["minute_of_day"] / 1440
    df["time_sin"] = np.sin(angle)
    df["time_cos"] = np.cos(angle)
    return df


def augment(df: pd.DataFrame, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Gaussian delay jitter (~±1–2 min) + arrival shift (±5 min), then recompute time features."""
    rng = np.random.default_rng(seed)
    df = df.copy()
    df["delay_min"] = np.clip(df["delay_min"] + rng.normal(0, 1.5, len(df)), 0, None)
    df["minute_of_day"] = (df["minute_of_day"] + rng.integers(-5, 6, len(df))) % 1440
    return add_cyclic_time(df)


def clean(df: pd.DataFrame, jitter: bool = True) -> pd.DataFrame:
    df = df.dropna().drop_duplicates().reset_index(drop=True)
    df = augment(df) if jitter else add_cyclic_time(df.copy())
    for col in CATEGORICAL_FEATURES:
        df[col] = df[col].astype(str)
    return df


def split_xy(df: pd.DataFrame):
    return df[FEATURES], df[TARGET]
