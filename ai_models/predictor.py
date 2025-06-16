import joblib
import pandas as pd
import os
from ai_models.features import extract_features_for_assignment
import shap
import matplotlib.pyplot as plt

MODEL_PATH = "ai_models/model.pkl"

_model_cache = {}  

def load_model(path=None):
    path = path or MODEL_PATH
    if path not in _model_cache:
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found at {path}")
        _model_cache[path] = joblib.load(path)
    return _model_cache[path]

def predict_assignment(assignment, model_path=None, features=None):
    model = load_model(model_path)


    features_dict = features or extract_features_for_assignment(assignment)


    try:
        writing_required = assignment.test.test_questions.filter(
            question__type__in=["code", "open"]
        ).exists()
        features_dict["writing_required"] = int(writing_required)
    except Exception:
        features_dict["writing_required"] = 0  # fallback in case of model/test mismatch


    if "mobile_detected_count" in features_dict:
        features_dict["mobile_detected_flag"] = int(features_dict["mobile_detected_count"] > 0)
    else:
        features_dict["mobile_detected_flag"] = 0

    features_dict["key_presses_per_min"] = features_dict.get("key_press_count", 0) / max(features_dict.get("actual_test_time_seconds", 60) / 60, 1)
    features_dict["typing_speed_suspect"] = int(
        features_dict.get("chars_per_minute", 0) > 500 and features_dict.get("key_press_count", 0) < 10
    )
    features_dict["total_gaze_offscreen"] = (
        features_dict.get("gaze_left_count", 0) +
        features_dict.get("gaze_right_count", 0) +
        features_dict.get("gaze_down_count", 0)
    )

    expected_features = model.get_booster().feature_names
    cleaned_features = {k: features_dict.get(k, 0) for k in expected_features}

    X = pd.DataFrame([cleaned_features], columns=expected_features)
    X.fillna(0, inplace=True)

    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    shap_impact = list(zip(X.columns, shap_values[0]))
    top_shap_features = sorted(shap_impact, key=lambda x: abs(x[1]), reverse=True)[:5]

    prediction = model.predict(X)[0]
    proba = model.predict_proba(X)[0][1]

    return {
        "cheating": bool(prediction),
        "probability": round(float(proba), 3),
        "top_factors": [
            {"feature": feat, "shap_value": round(val, 4)}
            for feat, val in top_shap_features
        ]
    }
