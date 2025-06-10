import random
from datetime import timedelta
from django.utils import timezone
from users.models.tests import (
    TestAssignment, StudentActivityLog, StudentActivityAnalysis, AudioAnalysis,
    StudentAnswer, TestQuestion
)
from users.models.questions import Question

def create_fake_assignment(student, test, cheating=False, noise_level=0.1):
    """
    Generează un TestAssignment fals, etichetat cu cheating sau nu, și injectează noise controlabil.
    """
    # === Creare assignment ===
    assignment = TestAssignment.objects.create(
        student=student,
        test=test,
        started_at=timezone.now(),
        finished_at=timezone.now() + timedelta(minutes=10),
        attempt_no=1,
        label=cheating
    )

    def noisy(value, variation):
        return value + random.uniform(-variation, variation)

    def flip(prob):
        return random.random() < prob

    # === Activity Analysis ===
    esc = 2 if cheating else (1 if flip(noise_level) else 0)
    second_screen = 2 if cheating else (1 if flip(noise_level) else 0)
    copy_paste = 5 if cheating else (random.randint(2, 4) if flip(noise_level) else random.randint(0, 1))
    key_presses = random.randint(5, 25) if cheating else (random.randint(20, 80) if flip(noise_level) else random.randint(150, 300))
    avg_delay = noisy(random.uniform(5, 40), 10)
    total_focus_lost = 3 if cheating else (1 if flip(noise_level) else 0)

    StudentActivityAnalysis.objects.create(
        assignment=assignment,
        attempt_no=1,
        esc_pressed=esc,
        second_screen_events=second_screen,
        tab_switches=random.randint(1, 3),
        window_blurs=random.randint(1, 2),
        copy_paste_events=copy_paste,
        total_key_presses=key_presses,
        average_key_delay=avg_delay,
        total_focus_lost=total_focus_lost,
        is_suspicious=cheating
    )

    # === Audio Analysis ===
    voiced_ratio = random.uniform(0.4, 0.7) if cheating else random.uniform(0.01, 0.05)
    if flip(noise_level):
        voiced_ratio *= random.uniform(0.8, 1.2)

    voiced_seconds = random.uniform(15, 70) if cheating else random.uniform(0, 8)
    AudioAnalysis.objects.create(
        assignment=assignment,
        attempt_no=1,
        voiced_ratio=voiced_ratio,
        voiced_seconds=voiced_seconds
    )

    # === StudentActivityLog (event logs) ===
    if cheating:
        for event_type in ["mobile_detected", "multiple_faces", "face_mismatch"]:
            StudentActivityLog.objects.create(
                assignment=assignment,
                attempt_no=1,
                focus_lost_count=1,
                anomaly_score=1.0,
                event_type=event_type,
                event_message=f"Simulated cheating: {event_type.replace('_', ' ')}"
            )
    else:
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=1,
            focus_lost_count=0,
            anomaly_score=0.0,
            event_type="face_match",
            event_message="Normal activity"
        )

    # === Fake Answers ===
    linked_questions = Question.objects.filter(testquestion__test=test)
    for question in linked_questions:
        answer_len = random.randint(300, 1000) if cheating else (random.randint(30, 300))
        if flip(noise_level) and not cheating:
            answer_len = random.randint(250, 600)

        StudentAnswer.objects.create(
            assignment=assignment,
            question=question,
            answer_text="a" * answer_len,
            needs_manual_review=False
        )

    return assignment
