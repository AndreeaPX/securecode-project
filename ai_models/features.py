from users.models.tests import StudentActivityLog, StudentActivityAnalysis, AudioAnalysis, StudentAnswer, TestQuestion
from users.models.questions import Question
from django.utils import timezone
from datetime import timedelta

def is_humanly_possible_writing(chars_per_minute, key_press_count, total_chars):
    if total_chars < 300:
        return 0
    if chars_per_minute > 700:
        return 1
    if chars_per_minute > 500 and key_press_count < 10:
        return 1
    return 0

def extract_features_for_assignment(assignment):
    attempt_no = assignment.attempt_no
    test = assignment.test
    use_proctoring = test.use_proctoring

    # ======================= AUDIO =======================
    if test.allow_sound_analysis:
        try:
            audio_analysis = AudioAnalysis.objects.get(assignment=assignment, attempt_no=attempt_no)
            voiced_seconds = audio_analysis.voiced_seconds
        except AudioAnalysis.DoesNotExist:
            voiced_seconds = 0.0

        logs = StudentActivityLog.objects.filter(assignment=assignment, attempt_no=attempt_no)
        voice_no_mouth_count = logs.filter(event_type="voice_no_mouth").count()
        too_much_talking_count = logs.filter(event_type="too_much_talking").count()
    else:
        voiced_seconds = 0.0
        voice_no_mouth_count = 0
        too_much_talking_count = 0

    # ======================= CAMERA =======================
    
    camera_logs = StudentActivityLog.objects.filter(assignment=assignment, attempt_no=attempt_no)

    multiple_faces_detected = camera_logs.filter(event_type="multiple_faces").count()
    face_mismatch_count = camera_logs.filter(event_type="face_mismatch").count()
    no_face_detected_count = camera_logs.filter(event_type="no_face_found").count()
    mobile_detected_count = camera_logs.filter(event_type="mobile_detected").count()
    gaze_left_count = camera_logs.filter(event_type="gaze_offscreen", event_message__icontains="left").count()
    gaze_right_count = camera_logs.filter(event_type="gaze_offscreen", event_message__icontains="right").count()
    if use_proctoring:
        gaze_down_count = camera_logs.filter(event_type="gaze_offscreen", event_message__icontains="down").count()
    else:
        gaze_down_count = 0

    # ======================= KEYBOARD & FOCUS =======================
    if test.has_ai_assistent:
        try:
            activity = StudentActivityAnalysis.objects.get(assignment=assignment, attempt_no=attempt_no)
        except StudentActivityAnalysis.DoesNotExist:
            activity = None

        esc_pressed = activity.esc_pressed if activity else 0
        second_screen = activity.second_screen_events if activity else 0
        tab_switches = activity.tab_switches if activity else 0
        window_blur = activity.window_blurs if activity else 0
        paste = activity.copy_paste_events if activity else 0
        key_presses = activity.total_key_presses if activity else 0
        avg_delay = activity.average_key_delay if activity else 0.0
        focus_lost = activity.total_focus_lost if activity else 0
    else:
        esc_pressed = 0
        second_screen = 0
        tab_switches = 0
        window_blur = 0
        paste = 0
        key_presses = 0
        avg_delay = 0.0
        focus_lost = 0

    # ======================= ANSWERS =======================
    answers = StudentAnswer.objects.filter(assignment=assignment)
    total_chars = sum(len(a.answer_text or "") for a in answers)

    question_ids = TestQuestion.objects.filter(test=test).values_list("question_id", flat=True)
    questions = Question.objects.filter(id__in=question_ids)
    q_types = questions.values_list("type", flat=True)
    writing_required = any(t in ("open", "code") for t in q_types)

    if assignment.started_at and assignment.finished_at and assignment.finished_at > assignment.started_at:
        actual_time = (assignment.finished_at - assignment.started_at).total_seconds()
    else:
        actual_time = (assignment.test.duration_minutes or 30) * 60

    chars_per_minute = total_chars / max(actual_time / 60, 1)
    impossible_writing = is_humanly_possible_writing(chars_per_minute, key_presses, total_chars)

    return {
        # AUDIO
        "voiced_seconds": round(voiced_seconds, 2),
        "mouth_open_no_voice_count": voice_no_mouth_count,
        "too_much_talking_count": too_much_talking_count,

        # CAMERA
        "multiple_faces_detected": multiple_faces_detected,
        "face_mismatch_count": face_mismatch_count,
        "no_face_detected_count": no_face_detected_count,
        "gaze_left_count": gaze_left_count,
        "gaze_right_count": gaze_right_count,
        "gaze_down_count": gaze_down_count,
        "mobile_detected_count": mobile_detected_count,

        # KEYBOARD
        "esc_pressed_count": esc_pressed,
        "second_screen_events": second_screen,
        "tab_switches_count": tab_switches,
        "window_blur_count": window_blur,
        "copy_paste_events": paste,
        "key_press_count": key_presses,
        "avg_key_delay": avg_delay,
        "focus_lost_total": focus_lost,
        "total_chars": total_chars,

        # CONTENT
        "actual_test_time_seconds": round(actual_time, 2),
        "chars_per_minute": round(chars_per_minute, 2),
        "is_impossible_writing_speed": impossible_writing,
        "writing_required": writing_required,
    }
