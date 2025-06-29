from __future__ import annotations
from collections import Counter
from typing import Dict, Any

from django.db.models import Q
from django.utils import timezone

from users.models.tests import (
    TestAssignment,
    StudentActivityLog,
    StudentActivityAnalysis,
    AudioAnalysis,
)
from users.models.questions import Question

def _gap(a, b, cap: int = 30) -> float:
    return min(abs((a - b).total_seconds()), cap)


def _impossible_writing(cpm: float, key_presses: int, chars: int) -> int:
    if chars < 300:
        return 0
    if cpm > 500:
        return 1
    if cpm > 350 and key_presses < chars * 0.4:
        return 1
    return 0


def extract_features_for_assignment(assignment: TestAssignment) -> Dict[str, Any]:
    test = assignment.test
    ai_enabled = test.has_ai_assistent
    audio_enabled = ai_enabled and test.allow_sound_analysis

    writing_required = Question.objects.filter(
        testquestion__test=test,
        type__in=["open", "code"],
    ).exists()

    # duration
    start = assignment.started_at or timezone.now()
    end = assignment.finished_at or timezone.now()
    duration_s = max((end - start).total_seconds(), 1)

    camera_logs = StudentActivityLog.objects.none()
    offscreen_sec = 0.0
    mobile_detected = multiple_faces_flag = face_mismatch_flag = no_face_flag = 0

    if ai_enabled:
        camera_logs = StudentActivityLog.objects.filter(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
        )
        counts = Counter(camera_logs.values_list("event_type", flat=True))
        mobile_detected = int(counts["mobile_detected"] > 0)
        multiple_faces_flag = int(counts["multiple_faces"] > 0)
        face_mismatch_flag = int(counts["face_mismatch"] > 0)
        no_face_flag = int(counts["no_face_found"] > 0)

        gaze_logs = camera_logs.filter(
            Q(event_type="gaze_offscreen") | Q(event_type="head_pose_suspicious")
        ).order_by("timestamp")
        prev = None
        for log in gaze_logs:
            if prev:
                offscreen_sec += _gap(log.timestamp, prev)
            prev = log.timestamp

    analysis = StudentActivityAnalysis.objects.filter(
        assignment=assignment,
        attempt_no=assignment.attempt_no,
    ).first()

    esc_pressed = analysis.esc_pressed if analysis else 0
    second_screen = analysis.second_screen_events if analysis else 0
    tab_switches = analysis.tab_switches if analysis else 0
    window_blurs = analysis.window_blurs if analysis else 0
    key_presses = analysis.total_key_presses if analysis else 0
    avg_delay = analysis.average_key_delay if analysis else 0.0
    total_chars = analysis.total_chars if analysis else 0

    cpm = total_chars / (duration_s / 60)
    copy_paste_ratio_flag = int(total_chars and key_presses < total_chars * 0.2 and writing_required)
    impossible_typing = _impossible_writing(cpm, key_presses, total_chars) if writing_required else 0

    voiced_seconds = voiced_ratio = speaking_too_much = 0.0
    if audio_enabled:
        audio = AudioAnalysis.objects.filter(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
        ).first()
        if audio:
            voiced_seconds = audio.voiced_seconds or 0.0
            voiced_ratio = audio.voiced_ratio or 0.0
            speaking_too_much = int(duration_s >= 90 and voiced_ratio >= 0.5)

    total_events = camera_logs.count() + (analysis.total_focus_lost if analysis else 0)
    activity_density = total_events / duration_s
    short_no_logs_flag = int(duration_s > 60 and total_events == 0)

    distilled = {
        "duration_seconds": duration_s,
        "writing_required": int(writing_required),
        "mobile_detected": mobile_detected,
        "multiple_faces_flag": multiple_faces_flag,
        "face_mismatch_flag": face_mismatch_flag,
        "no_face_flag": no_face_flag,
        "offscreen_seconds": offscreen_sec,
        "copy_paste_ratio": copy_paste_ratio_flag,
        "impossible_typing": impossible_typing,
        "voiced_seconds": voiced_seconds,
        "voiced_ratio": voiced_ratio,
        "speaking_too_much": speaking_too_much,
        "activity_density": round(activity_density, 4),
        "short_session_no_logs": short_no_logs_flag,
    }

    modality_flags = {
        "has_ai_assistent": int(test.has_ai_assistent),   
        "allow_sound_analysis": int(test.allow_sound_analysis),  
        "use_proctoring": int(test.use_proctoring),           
    }

    raw = {
        "voiced_seconds": round(voiced_seconds, 2),
        "mobile_detected_count": mobile_detected,
        "multiple_faces_detected": multiple_faces_flag,
        "face_mismatch_count": face_mismatch_flag,
        "no_face_detected_count": no_face_flag,
        "esc_pressed_count": esc_pressed,
        "second_screen_events": second_screen,
        "tab_switches_count": tab_switches,
        "window_blur_count": window_blurs,
        "key_press_count": key_presses,
        "total_chars": total_chars,
        "avg_key_delay": avg_delay,
        "chars_per_minute": round(cpm, 2),
        "offscreen_seconds": offscreen_sec,
    }

    return {
        "features": {**distilled, **modality_flags},
        "raw": raw,
    }
