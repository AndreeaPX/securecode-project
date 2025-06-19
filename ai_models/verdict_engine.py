from ai_models.predictor import predict_assignment
from ai_models.features import extract_features_for_assignment
from users.models.tests import StudentActivityLog


def apply_rules(features, *, proctoring: bool = False) -> tuple[bool, str | None]:
    duration = max(features.get("actual_test_time_seconds", 60.0), 60.0)
    offscreen_sec = features.get("offscreen_seconds", 0.0)
    offscreen_pct = offscreen_sec / duration
    print(offscreen_sec)
    print(offscreen_pct)
    if offscreen_pct >= 0.60:
        return True, f"Looked away for {offscreen_pct:.0%} of the test"

    if not features.get("writing_required", False) and offscreen_pct >= 0.50:
        return True, f"Looked away {offscreen_pct:.0%} of the quiz (no writing expected)"

    if features.get("mobile_detected_count", 0) > 0:
        return True, "Phone detected in camera"

    if features.get("multiple_faces_detected", 0) >= 2:
        return True, "Multiple faces detected repeatedly"

    if features.get("face_mismatch_count", 0) >= 2:
        return True, "Face mismatch detected repeatedly"

    if features.get("voiced_seconds", 0) > 0.5 * duration and features.get("gaze_down_count", 0) > 0 and features.get("writting_required", False):
        return True, "Spoke extensively while looking down — potential off-device conversation"

    if features.get("writing_required", False):
        if features.get("chars_per_minute", 0) > 700 and features.get("key_press_count", 0) < 10:
            return True, "Answer pasted too fast to be typed"

        if features.get("key_press_count", 0) == 0 and features.get("total_chars", 0) > 0:
            return True, "Text entered while no key-presses recorded"

    if proctoring:
        if features.get("tab_switches_count", 0) > 2:
            return True, "Switched tabs 3+ times"

        if features.get("esc_pressed_count", 0) > 2:
            return True, "Pressed ESC 3+ times"

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

    
    duration = features.get("actual_test_time_seconds", 600)
    if features.get("voiced_seconds", 0) < 0.5 * duration:
        features["voiced_seconds"] = 0

    cheating, reason = apply_rules(features, proctoring=test.use_proctoring)
    if cheating:
        return {
            "cheating": True,
            "certainty": "high",
            "reason": f"Rule triggered: {reason}",
            "rule_triggered": True,
            "rule_reason": reason,
            "top_factors": []
        }
    
    logs = StudentActivityLog.objects.filter(
    assignment=assignment,
    attempt_no=assignment.attempt_no
    ).values_list("event_type", flat=True)

    log_types = list(logs)

    only_face_match_or_no_logs = (
        len(log_types) == 0 or all(event == "face_match" for event in log_types)
    )

    if only_face_match_or_no_logs :
        return {
        "cheating": False,
        "certainty": "high",
        "reason": "Only non-suspicious logs (face_match) and no input — test clean",
        "rule_triggered": False,
        "top_factors": [],
        }

    prediction = predict_assignment(assignment, features=features)
    proba = prediction["probability"]

    if prediction["cheating"] and features.get("voiced_seconds", 0) > 10:
        voice_only = all(
            features.get(k, 0) == 0 for k in [
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