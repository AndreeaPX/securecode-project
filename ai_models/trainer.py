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

MODEL_PATH = "ai_models/model.pkl"

def get_labeled_data():
    assignments = TestAssignment.objects.filter(label__isnull=False)
    data = []
    labels = []

    for assignment in assignments:
        features = extract_features_for_assignment(assignment)
        if features:
            data.append(features)
            labels.append(int(not assignment.label))  # 1 = cheating, 0 = legit

    return pd.DataFrame(data), pd.Series(labels)

def train_and_save_model():
    X, y = get_labeled_data()

    if len(X) < 10:
        print("[WARN] Too few labeled samples to train model.")
        return

    # --- Clean-up & Transformations ---
    X.drop(columns=["voiced_ratio"], errors='ignore', inplace=True)
    X["voiced_seconds"] = X["voiced_seconds"].clip(upper=20)
    X["focus_lost_total"] = (X["focus_lost_total"] > 1).astype(int)
    X["mobile_detected_flag"] = (X["mobile_detected_count"] > 0).astype(int)
    X.drop(columns=["mobile_detected_count"], inplace=True)

    # --- Derived Features ---
    X["key_presses_per_min"] = X["key_press_count"] / (X["actual_test_time_seconds"] / 60)
    X["typing_speed_suspect"] = ((X["chars_per_minute"] > 500) & (X["key_press_count"] < 10)).astype(int)
    X["total_gaze_offscreen"] = X["gaze_left_count"] + X["gaze_right_count"] + X["gaze_down_count"]

    # Drop redundant/noisy cols that might be missing or unhelpful
    X.drop(columns=[
        "gaze_left_count", "gaze_right_count", "gaze_down_count",
        "gaze_unclear_count", "chars_per_second", "avg_key_delay",
        "voice_detected_count", "mouth_open_no_voice_count"  # explicit nuke of unstable cols
    ], errors='ignore', inplace=True)

    # --- Train/Test Split ---
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

    # --- Save Model ---
    joblib.dump(model, MODEL_PATH)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    benchmark_path = f"ai_models/model_versions/model_{timestamp}.pkl"
    shutil.copy(MODEL_PATH, benchmark_path)
    print(f"\n✅ Benchmark model saved at: {benchmark_path}")
    print(f"[OK] Model trained and saved to {MODEL_PATH}")

    # --- Feature Importance ---
    imp = pd.Series(model.feature_importances_, index=X.columns)
    print("\n🔥 Top Features:")
    print(imp.sort_values(ascending=False).head(10))

    # --- Evaluation ---
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"\n✅ Accuracy: {round(acc * 100, 2)}%")
    print("\n📊 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Legit", "Cheating"]))

    cm = confusion_matrix(y_test, y_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=["Legit", "Cheating"],
                yticklabels=["Legit", "Cheating"])
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.title("Confusion Matrix")
    plt.show()
