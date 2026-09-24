"""The three regressors from the paper behind one small registry."""
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

from app.config import CATBOOST_PARAMS, CATEGORICAL_FEATURES, RF_PARAMS, XGB_PARAMS


def _encoder() -> ColumnTransformer:
    # Trees are fine with ordinal codes; unseen IDs become -1 at inference time
    return ColumnTransformer(
        [("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
          CATEGORICAL_FEATURES)],
        remainder="passthrough",
    )


def random_forest():
    return Pipeline([("enc", _encoder()), ("model", RandomForestRegressor(**RF_PARAMS))])


def xgboost():
    from xgboost import XGBRegressor
    return Pipeline([("enc", _encoder()), ("model", XGBRegressor(**XGB_PARAMS))])


def catboost():
    # CatBoost handles categorical columns natively — no encoder needed
    from catboost import CatBoostRegressor
    return CatBoostRegressor(cat_features=CATEGORICAL_FEATURES, **CATBOOST_PARAMS)


REGISTRY = {"RandomForest": random_forest, "XGBoost": xgboost, "CatBoost": catboost}
