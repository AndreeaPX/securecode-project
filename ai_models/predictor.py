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

def predict_assignment(assignment, model_path=None):
    model = load_model(model_path)

    features_dict = extract_features_for_assignment(assignment)
    X = pd.DataFrame([features_dict])
    X.fillna(0, inplace=True)

    # SHAP explanation
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(X)
    shap_impact = list(zip(X.columns, shap_values[0]))
    top_shap_features = sorted(shap_impact, key=lambda x: abs(x[1]), reverse=True)[:3]

    # Prediction
    prediction = model.predict(X)[0]  # 0 = legit, 1 = cheating
    proba = model.predict_proba(X)[0][1]  # Prob of class 1 = cheating

    # Optional SHAP visual for debugging or admin UI
    shap.initjs()
    shap.force_plot(explainer.expected_value, shap_values[0], X.iloc[0], matplotlib=True)
    plt.show()

    return {
        "predicted_cheating": bool(prediction),
        "probability": round(float(proba), 3),
        "top_factors": [
            {"feature": feat, "shap_value": round(val, 4)}
            for feat, val in top_shap_features
        ]
    }
