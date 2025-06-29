from __future__ import annotations
import os
import joblib
import pandas as pd
import shap

from ai_models.features import extract_features_for_assignment

MODEL_PATH = "ai_models/model.pkl"
_model_cache: dict[str, object] = {}


# --------------------------------------------------------------------- utils
def _flatten(fdict: dict) -> dict:
    """Merge {'features':…, 'raw':…} into one dict if needed."""
    if isinstance(fdict, dict) and "features" in fdict and "raw" in fdict:
        merged = fdict["features"].copy()
        merged.update(fdict["raw"])
        return merged
    return fdict


def load_model(path: str | None = None):
    path = path or MODEL_PATH
    if path not in _model_cache:
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model not found at {path}. "
                "Train one via ai_models.trainer.train_and_save_model()."
            )
        _model_cache[path] = joblib.load(path)
    return _model_cache[path]


# ---------------------------------------------------------------- predictor
def predict_assignment(
    assignment,
    *,
    model_path: str | None = None,
    features: dict | None = None,
):
    model = load_model(model_path)

    # -------- feature extraction & flatten --------------
    features_dict = _flatten(features or extract_features_for_assignment(assignment))

    # -------- lightweight derived helpers --------------
    duration = features_dict.get("duration_seconds", 60.0)

    features_dict["mobile_detected_flag"] = int(
        features_dict.get("mobile_detected_count", features_dict.get("mobile_detected", 0))
        > 0
    )
    features_dict["key_presses_per_min"] = (
        features_dict.get("key_press_count", 0) / max(duration / 60.0, 1)
    )
    features_dict["typing_speed_suspect"] = int(
        features_dict.get("chars_per_minute", 0) > 500
        and features_dict.get("key_press_count", 0) < 10
    )
    features_dict["total_gaze_offscreen"] = (
        features_dict.get("gaze_left_count", 0)
        + features_dict.get("gaze_right_count", 0)
        + features_dict.get("gaze_down_count", 0)
    )

    # -------- align with model input --------------------
    expected = model.get_booster().feature_names
    cleaned = {k: features_dict.get(k, 0) for k in expected}
    X = pd.DataFrame([cleaned], columns=expected).fillna(0)

    # -------- SHAP explainability -----------------------
    explainer = shap.TreeExplainer(model)
    shap_vals = explainer.shap_values(X)[0]
    top_factors = sorted(
        zip(X.columns, shap_vals), key=lambda x: abs(x[1]), reverse=True
    )[:5]

    # -------- prediction --------------------------------
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0][1]

    return {
        "cheating": bool(pred),
        "probability": round(float(proba), 3),
        "top_factors": [
            {"feature": f, "shap_value": round(v, 4)} for f, v in top_factors
        ],
    }
