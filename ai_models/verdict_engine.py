from ai_models.predictor import predict_assignment

def apply_rules(features, test_has_proctoring=False):
    if test_has_proctoring:
        if features.get("esc_pressed_count", 0) >= 2:
            return True, "Pressed ESC 2+ times"
        if features.get("second_screen_events", 0) >= 2:
            return True, "Used second screen 2+ times"

    if features.get("mobile_detected_count", 0) > 0:
        return True, "Phone detected in camera"
    if features.get("multiple_faces_detected", 0) >= 2:
        return True, "Multiple faces detected multiple times"
    if features.get("face_mismatch_count", 0) >= 2:
        return True, "Face mismatch occurred repeatedly"
    if features.get("copy_paste_events", 0) > 3 and features.get("avg_key_delay", 100) < 30:
        return True, "High copy-paste with low typing effort"
    if features.get("chars_per_minute", 0) > 700 and features.get("key_press_count", 0) < 10:
        return True, "Answer pasted too fast to be typed"
    if features.get("voiced_ratio", 0) > 0.3 and features.get("mouth_open_no_voice_count", 0) > 2:
        return True, "Talking without visible mouth movement"
    if (
        features.get("gaze_down_count", 0) >= 2 and
        features.get("head_down_count", 0) >= 2 and
        features.get("voice_detected_count", 0) > 1
    ):
        return True, "Reading something off-screen while speaking"

    return False, None

def get_verdict_for_assignment(assignment):
    from ai_models.features import extract_features_for_assignment
    test = assignment.test

    if not (test.use_proctoring or test.has_ai_assistent or test.allow_sound_analysis):
        return {
            "cheating": False,
            "certainty": "unknown",
            "reason": "Test does not support AI evaluation"
        }

    features = extract_features_for_assignment(assignment)

    # Apply hard rules
    cheating, reason = apply_rules(features, test_has_proctoring=test.use_proctoring)
    if cheating:
        return {
            "cheating": True,
            "certainty": "high",
            "reason": f"Rule triggered: {reason}"
        }

    # Predict using AI
    prediction = predict_assignment(assignment)

    # Override if prediction is weak
    proba = prediction["probability"]
    if 0.4 < proba < 0.55:
        return {
            "cheating": False,
            "certainty": "low",
            "reason": "AI not confident enough to classify as cheating",
            "probability": proba,
            "top_factors": prediction["top_factors"]
        }

    return {
        "cheating": prediction["predicted_cheating"],
        "certainty": "medium" if 0.4 < proba < 0.7 else "high",
        "probability": proba,
        "top_factors": prediction["top_factors"],
        "reason": "AI-based classification"
    }
