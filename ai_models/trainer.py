from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import joblib
from xgboost import XGBClassifier
from users.models.tests import TestAssignment
from ai_models.features import extract_features_for_assignment
import shutil
from datetime import datetime
from imblearn.over_sampling import SMOTE
import numpy as np


MODEL_PATH = "ai_models/model.pkl"

def add_derived_features(features):
        # Derive the same flags the predictor expects
    features["mobile_detected_flag"] = int(features.get("mobile_detected_count", 0) > 0)
    features["key_presses_per_min"] = features.get("key_press_count", 0) / max(features.get("actual_test_time_seconds", 60) / 60,1,)

    features["typing_speed_suspect"] = int(features.get("chars_per_minute", 0) > 500 and features.get("key_press_count", 0) < 10)

    features["total_gaze_offscreen"] = (
        features.get("gaze_left_count", 0)
        + features.get("gaze_right_count", 0)
        + features.get("gaze_down_count", 0)
    )
    return features


def get_labeled_data():
    assignments = TestAssignment.objects.filter(label__isnull=False)
    data = []
    labels = []

    for assignment in assignments:
        features = extract_features_for_assignment(assignment)
        duration = features.get("actual_test_time_seconds", 600)
        if features.get("voiced_seconds",0) < 0.5 * duration:
            features["voiced_seconds"] = 0

        if "total_chars" not in features:
            from users.models.tests import StudentAnswer
            total_chars = sum(len(a.answer_text or "") for a in StudentAnswer.objects.filter(assignment=assignment))
            features["total_chars"] = total_chars


        features = add_derived_features(features=features)

        if features:
            data.append(features)
            labels.append(int(not assignment.label))  # 1 = cheating, 0 = legit

    return pd.DataFrame(data), pd.Series(labels)


def train_and_save_model():
    X, y = get_labeled_data()

    if len(X) < 10:
        print("[WARN] Too few labeled samples to train model.")
        return
    
    X["key_presses_per_min"] = np.log1p(X["key_presses_per_min"])
    X["chars_per_minute"] = np.log1p(X["chars_per_minute"])
    X["voiced_seconds"] = X["voiced_seconds"].clip(upper=20)
    X["focus_lost_total"] = (X["focus_lost_total"] > 1).astype(int)


# Anything that rules would ALWAYS flag as cheating is removed from training
    rule_violations = (
    (X.get("mobile_detected_count", 0) > 0)
    | (X.get("multiple_faces_detected", 0) >= 2)
    | (X.get("face_mismatch_count", 0) >= 2)
    | ((X.get("chars_per_minute", 0) > 700) & (X.get("key_press_count", 0) < 10))
    | ((X.get("key_press_count", 0) == 0) & (X.get("total_chars", 0) > 0))
    | ((X.get("copy_paste_events", 0) > 3) & (X.get("avg_key_delay", 100) < 30))
    | (
        (X.get("voiced_seconds", 0) > 30)
        & (X.get("mouth_open_no_voice_count", 0) > 2)
    )
    )

    X = X[~rule_violations]
    y = y.loc[X.index]

    smote = SMOTE(random_state=42)
    X, y = smote.fit_resample(X, y)


    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        eval_metric="logloss",
        random_state=42
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    joblib.dump(model, MODEL_PATH)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    benchmark_path = f"ai_models/model_versions/model_{timestamp}.pkl"
    shutil.copy(MODEL_PATH, benchmark_path)
    print(f"\n✅ Benchmark model saved at: {benchmark_path}")
    print(f"[OK] Model trained and saved to {MODEL_PATH}")

    imp = pd.Series(model.feature_importances_, index=X.columns)
    print("\nTop Features:")
    print(imp.sort_values(ascending=False).head(10))


    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {round(acc * 100, 2)}%")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Cheating"]))

    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=["Legit", "Cheating"],
                yticklabels=["Legit", "Cheating"])
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.show()
