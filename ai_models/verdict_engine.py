from ai_models.predictor import predict_assignment
from ai_models.features import extract_features_for_assignment

def apply_rules(features, test_has_proctoring=False):
    # --- Universal hard flags -----------------------------------------
    if features.get("mobile_detected_count", 0) > 0:
        return True, "Phone detected in camera"
    if features.get("multiple_faces_detected", 0) >= 2:
        return True, "Multiple faces detected multiple times"
    if features.get("face_mismatch_count", 0) >= 2:
        return True, "Face mismatch occurred repeatedly"
    
    if (
        features.get("chars_per_minute", 0) > 700
        and features.get("key_press_count", 0) < 10
    ):
        return True, "Answer pasted too fast to be typed"
    
    if (
        features.get("key_press_count", 0) == 0
        and features.get("total_chars", 0) > 0
    ):
        return True, "Text entered while no key-presses recorded"

    # --- Proctoring-only rules ----------------------------------------
    if test_has_proctoring:
        if features.get("esc_pressed_count", 0) >= 2:
            return True, "Pressed ESC 2+ times"
        if features.get("second_screen_events", 0) >= 2:
            return True, "Used second screen 2+ times"
        if features.get("focus_lost_total", 0) >= 2:
            return True, "Test lost focus 2+ times"
        if features.get("tab_switches_count", 0) >= 2:
            return True, "Switched tabs 2+ times"
        
        # voice-only based flag (now stricter, requires *multiple signs*)
        if (
            features.get("voiced_seconds", 0) > 50
            and features.get("mouth_open_no_voice_count", 0) > 2
        ):
            return True, "Talking without visible mouth movement"

        if (
            not features.get("writing_required", False)
            and features.get("gaze_down_count", 0) >= 2
            and features.get("head_down_count", 0) >= 2
            and features.get("voice_detected_count", 0) > 1
        ):
            return True, "Reading something off-screen while speaking"

    # --- All good
    return False, None


def get_verdict_for_assignment(assignment, features=None):
    test = assignment.test

    if not (test.use_proctoring or test.has_ai_assistent or test.allow_sound_analysis):
        return {
            "cheating": False,
            "certainty": "unknown",
            "reason": "Test does not support AI evaluation"
        }

    features = features or extract_features_for_assignment(assignment)

    # 🚨 Apply hard rules first — these override AI completely
    cheating, reason = apply_rules(features, test_has_proctoring=test.use_proctoring)
    if cheating:
        return {
            "cheating": True,
            "certainty": "high",
            "reason": f"Rule triggered: {reason}",
            "rule_triggered": True,
            "rule_reason": reason,
            "top_factors": []  # optional SHAP override if needed
        }

    # 🤖 If no rules triggered, fall back to AI model
    prediction = predict_assignment(assignment, features=features)
    proba = prediction["probability"]
    # 🚫 Voice-only cheating override — if only voice is flagged but no other red flags
    if prediction["cheating"] and features.get("voiced_seconds", 0) > 10:
        voice_only = all(
            features.get(k, 0) == 0
            for k in [
                "copy_paste_events",
                "multiple_faces_detected",
                "mobile_detected_count",
                "face_mismatch_count",
                "esc_pressed_count",
                "second_screen_events",
                "tab_switches_count",
                "window_blur_count"
            ]
        )
        if voice_only:
            prediction["cheating"] = False
            prediction["certainty"] = "low"
            prediction["reason"] = "Voice detected, but no other suspicious behavior"

    
    if proba <= 0.4:
        return {
            "cheating": False,
            "certainty": "high" if proba < 0.2 else "medium",
            "reason": "AI-based classification",
            "probability": proba,
            "top_factors": prediction["top_factors"]
        }

    if 0.4 < proba <= 0.55:
        return {
            "cheating": False,
            "certainty": "low",
            "reason": "AI not confident enough to classify as cheating",
            "probability": proba,
            "top_factors": prediction["top_factors"]
        }


    return {
        "cheating": prediction["cheating"],
        "certainty": "medium" if 0.4 < proba < 0.7 else "high",
        "probability": proba,
        "top_factors": prediction["top_factors"],
        "reason": "AI-based classification"
    }
