from __future__ import annotations
import os, shutil
from datetime import datetime
from typing import Dict, Any
import joblib, numpy as np, pandas as pd, seaborn as sns, matplotlib.pyplot as plt
from imblearn.over_sampling import SMOTE
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from ai_models.features import extract_features_for_assignment
from users.models.tests import TestAssignment

MODEL_PATH = "ai_models/model.pkl"


def _flatten(fdict: dict) -> dict:
    if "features" in fdict and "raw" in fdict:
        flat = fdict["features"].copy()
        flat.update(fdict["raw"])
        return flat
    return fdict

def add_derived_features(features: Dict[str, Any]) -> Dict[str, Any]:
    flat = _flatten(features)
    return _add_derived(flat)

def _add_derived(feat: dict) -> dict:
    duration_min = max(feat.get("duration_seconds", 60) / 60, 1)
    duration_sec = max(feat.get("duration_seconds", 60), 1)
    feat["voiced_ratio"] = feat.get("voiced_seconds", 0) / duration_sec
    feat["voiced_ratio"] = min(feat["voiced_ratio"], 1.0)

    # Existing
    feat["mobile_detected_flag"] = int(
        feat.get("mobile_detected_count", feat.get("mobile_detected", 0)) > 0
    )
    feat["key_presses_per_min"] = feat.get("key_press_count", 0) / duration_min
    feat["typing_speed_suspect"] = int(
        feat.get("chars_per_minute", 0) > 500 and feat.get("key_press_count", 0) < 10
    )

    # Normalized versions of noisy but useful signals
    feat["no_face_ratio"] = feat.get("no_face_detected_count", 0) / duration_min
    feat["multiple_faces_rate"] = feat.get("multiple_faces_detected", 0) / duration_min
    feat["face_mismatch_rate"] = feat.get("face_mismatch_count", 0) / duration_min
    feat["offscreen_ratio"] = feat.get("offscreen_seconds", 0) / (duration_min * 60)
    feat["gaze_offscreen_total"] = (
        feat.get("gaze_left_count", 0)
        + feat.get("gaze_right_count", 0)
        + feat.get("gaze_down_count", 0)
    ) / duration_min

    feat["voiced_ratio"] = min(feat["voiced_ratio"], 0.8)
    feat["offscreen_ratio"] = min(feat["offscreen_ratio"], 1.0)
    feat["multiple_faces_rate"] = min(feat["multiple_faces_rate"], 1.0)
    feat["face_mismatch_rate"] = min(feat["face_mismatch_rate"], 1.0)

    return feat



# ───────────────────────────── data gathering ───────────────────────────────
def get_labeled_data() -> tuple[pd.DataFrame, pd.Series]:
    qs = TestAssignment.objects.filter(label__isnull=False)
    rows, labels = [], []

    for a in qs.iterator():
        feat = _flatten(extract_features_for_assignment(a))

        # mute tiny voice fragments (keeps behaviour from verdict engine)
        dur = feat.get("duration_seconds", 600)
        if feat.get("voiced_seconds", 0) < 0.5 * dur:
            feat["voiced_seconds"] = 0

        # ensure total_chars present for typing heuristics
        if "total_chars" not in feat:
            from users.models.tests import StudentAnswer
            feat["total_chars"] = sum(
                len(ans.answer_text or "")
                for ans in StudentAnswer.objects.filter(assignment=a)
            )

        rows.append(_add_derived(feat))
        labels.append(int(not a.label))  # 1 = cheating, 0 = legit

    return pd.DataFrame(rows), pd.Series(labels)


# ──────────────────────────────── trainer ───────────────────────────────────
def train_and_save_model() -> None:
    X, y = get_labeled_data()
    X = X.apply(pd.to_numeric, errors="coerce").fillna(0)

    if len(X) < 10:
        print("[WARN] Too few labelled samples to train.")
        return

    # light transforms
    X["chars_per_minute"] = np.log1p(X["chars_per_minute"])
    X["voiced_seconds"] = X["voiced_seconds"].clip(upper=20)

    # ── OPTIONAL RULE PRUNE ──
    # Uncomment this block if you ever want to drop cases
    # the deterministic rules would flag with 100 % certainty.
    #
    # RULE_VIOLATIONS = (
    #     (X["mobile_detected_count"] > 0)
    #     | (X["multiple_faces_detected"] >= 2)
    #     | (X["face_mismatch_count"] >= 2)
    #     | ((X["chars_per_minute"] > np.log1p(700)) & (X["key_press_count"] < 10))
    #     | ((X["key_press_count"] == 0) & (X["total_chars"] > 0))
    #     | (X["tab_switches_count"] >= 2)
    #     | (X["second_screen_events"] >= 2)
    #     | (X["esc_pressed_count"] >= 2)
    # )
    # X, y = X.loc[~RULE_VIOLATIONS], y.loc[~RULE_VIOLATIONS]

    DROP_COLS = [
        "has_ai_assistent", "use_proctoring", "allow_sound_analysis",
        "no_face_flag", "multiple_faces_flag", "face_mismatch_flag",
        "mobile_detected_flag", "typing_speed_suspect",
        "multiple_faces_detected", "face_mismatch_count", "mobile_detected_count",
        "offscreen_seconds", "no_face_detected_count",
        "gaze_left_count", "gaze_right_count", "gaze_down_count",
        "voiced_seconds"
    ]

    X = X.drop(columns=[c for c in DROP_COLS if c in X.columns])


    # balance dataset
    X_res, y_res = SMOTE(random_state=42).fit_resample(X, y)

    # split
    X_tr, X_te, y_tr, y_te = train_test_split(
        X_res, y_res, test_size=0.2, random_state=42, stratify=y_res
    )

    # model
    model = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        eval_metric="logloss",
        random_state=42,
    )
    model.fit(X_tr, y_tr, eval_set=[(X_te, y_te)], verbose=False)

    # persist
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    bench_path = f"ai_models/model_versions/model_{ts}.pkl"
    os.makedirs(os.path.dirname(bench_path), exist_ok=True)
    shutil.copy(MODEL_PATH, bench_path)

    # quick report
    y_pred = model.predict(X_te)
    acc = accuracy_score(y_te, y_pred)
    print(f"✅  Model saved ({acc*100:0.2f}% acc).  Bench: {bench_path}")

    # print("\nTop 10 features:")
    # imp = pd.Series(model.feature_importances_, index=X.columns)
    # print(imp.sort_values(ascending=False).head(10))

    # cm = confusion_matrix(y_te, y_pred)
    # sns.heatmap(
    #     cm,
    #     annot=True,
    #     fmt="d",
    #     cmap="Blues",
    #     xticklabels=["Legit", "Cheating"],
    #     yticklabels=["Legit", "Cheating"],
    # )
    # plt.xlabel("Predicted")
    # plt.ylabel("Actual")
    # plt.title("Confusion Matrix")
    # plt.show()
