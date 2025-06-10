def create_balanced_training_batch(student, test, num_per_type=10):
    from users.models.tests import TestAssignment
    from datetime import timedelta
    from django.utils import timezone
    import random
    from users.models.tests import (
        StudentActivityLog, StudentActivityAnalysis,
        AudioAnalysis, StudentAnswer
    )
    from users.models.questions import Question

    def create_assignment(label):
        return TestAssignment.objects.create(
            student=student,
            test=test,
            started_at=timezone.now(),
            finished_at=timezone.now() + timedelta(minutes=10),
            attempt_no=1,
            label=label
        )

    def add_analysis(a, **kwargs):
        StudentActivityAnalysis.objects.create(
            assignment=a,
            attempt_no=1,
            esc_pressed=kwargs.get("esc", 0),
            second_screen_events=kwargs.get("screen", 0),
            tab_switches=random.randint(1, 3),
            window_blurs=random.randint(0, 2),
            copy_paste_events=kwargs.get("paste", 0),
            total_key_presses=kwargs.get("keys", 150),
            average_key_delay=kwargs.get("delay", 50),
            total_focus_lost=kwargs.get("focus", 0),
            is_suspicious=kwargs.get("sus", False)
        )

    def add_audio(a, voiced_ratio, mouth_silent):
        AudioAnalysis.objects.create(
            assignment=a,
            attempt_no=1,
            voiced_ratio=voiced_ratio,
            voiced_seconds=voiced_ratio * 90,
            mouth_open_no_voice_count=mouth_silent
        )

    def add_logs(a, events):
        for ev in events:
            StudentActivityLog.objects.create(
                assignment=a,
                attempt_no=1,
                focus_lost_count=1,
                anomaly_score=1.0,
                event_type=ev,
                event_message=f"Simulated event: {ev.replace('_', ' ')}"
            )

    def add_answers(a, short=False):
        questions = Question.objects.filter(testquestion__test=test)
        for q in questions:
            StudentAnswer.objects.create(
                assignment=a,
                question=q,
                answer_text="X" * random.randint(80, 120) if short else "X" * random.randint(500, 1000),
                needs_manual_review=False
            )

    for _ in range(num_per_type):
        # 1. Legit no issues
        a = create_assignment(False)
        add_analysis(a)
        add_audio(a, 0.01, 0)
        add_logs(a, [])
        add_answers(a)

        # 2. False positive (some noise)
        a = create_assignment(False)
        add_analysis(a, esc=1, screen=1, paste=2, delay=25, keys=80, focus=1, sus=True)
        add_audio(a, 0.2, 1)
        add_logs(a, ["gaze_offscreen"])
        add_answers(a)

        # 3. True cheating
        a = create_assignment(True)
        add_analysis(a, esc=3, screen=2, paste=6, delay=10, keys=15, focus=3, sus=True)
        add_audio(a, 0.5, 3)
        add_logs(a, ["mobile_detected", "face_mismatch", "multiple_faces"])
        add_answers(a)

        # 4. Edge cheating (could slip through AI)
        a = create_assignment(True)
        add_analysis(a, esc=0, screen=0, paste=4, delay=35, keys=300, focus=0, sus=True)
        add_audio(a, 0.4, 0)
        add_logs(a, ["head_pose_suspicious"])
        add_answers(a)
