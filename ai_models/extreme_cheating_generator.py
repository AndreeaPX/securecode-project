import random
from datetime import timedelta
from django.utils import timezone
from users.models.tests import (
    TestAssignment, StudentActivityLog, StudentActivityAnalysis,
    AudioAnalysis, StudentAnswer
)
from users.models.questions import Question

def create_extreme_cheating_assignment(student, test):
    assignment = TestAssignment.objects.create(
        student=student,
        test=test,
        started_at=timezone.now(),
        finished_at=timezone.now() + timedelta(minutes=10),
        attempt_no=1,
        label=True
    )

    # Activity analysis
    StudentActivityAnalysis.objects.create(
        assignment=assignment,
        attempt_no=1,
        esc_pressed=random.randint(0, 6),
        second_screen_events=random.randint(3, 5),
        tab_switches=random.randint(5, 15),
        window_blurs=random.randint(5, 15),
        copy_paste_events=random.randint(10, 20),
        total_key_presses=random.randint(3, 15),
        average_key_delay=random.uniform(1, 10),
        total_focus_lost=random.randint(5, 10),
        is_suspicious=True
    )

    # Audio
    AudioAnalysis.objects.create(
        assignment=assignment,
        attempt_no=1,
        voiced_ratio=random.uniform(0.5, 0.9),
        voiced_seconds=random.uniform(90, 180),
        mouth_open_no_voice_count=random.randint(3, 6)
    )

    # Event logs
    extreme_events = random.sample([
        "mobile_detected",
        "multiple_faces",
        "face_mismatch",
        "gaze_offscreen",
        "gaze_down",
        "head_pose_suspicious",
        "no_face_found",
        "voice_detected",
        "too_much_talking"
    ], k=random.randint(5, 9))  # Variază combinațiile

    for event_type in extreme_events:
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=1,
            focus_lost_count=1,
            anomaly_score=1.0,
            event_type=event_type,
            event_message=f"Extreme cheating: {event_type.replace('_', ' ')}"
        )

    # Fake answers
    linked_questions = Question.objects.filter(testquestion__test=test)
    for question in linked_questions:
        answer_text = "🧠" * random.randint(1000, 2000)
        StudentAnswer.objects.create(
            assignment=assignment,
            question=question,
            answer_text=answer_text,
            needs_manual_review=True
        )

    return assignment
