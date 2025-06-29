# scripts/generate_training_samples.py
# -----------------------------------
# Usage:
#   python manage.py shell < scripts/generate_training_samples.py
#
# This will create four synthetic assignments:
#   • 2 for “attachment test” (writing required)
#   • 2 for “Quizz Test Database Sec (Training)” (no writing)
#   Each pair has one legit sample and one obvious-cheating sample.
#
# Feel free to duplicate / tweak the SCENARIOS list to add more variety.

from datetime import timedelta
import random

from django.utils import timezone

from users.models import User
from users.models.tests import (
    TestAssignment,
    StudentActivityLog,
    StudentActivityAnalysis,
    AudioAnalysis,
    StudentAnswer,
    Test,
)
from users.models.questions import Question
from users.views.mouse_keyboard_view import analyze_assignment_logs


# ----------  low-level helpers ---------------------------------------------

def make_assignment(student, test, *, label: bool) -> TestAssignment:
    return TestAssignment.objects.create(
        student=student,
        test=test,
        started_at=timezone.now(),
        finished_at=timezone.now() + timedelta(minutes=10),
        attempt_no=1,
        label=label,
    )


def add_answers(a: TestAssignment, *, short: bool):
    for q in Question.objects.filter(testquestion__test=a.test):
        StudentAnswer.objects.create(
            assignment=a,
            question=q,
            answer_text="X" * random.randint(80, 120) if short else "X" * random.randint(600, 1200),
            needs_manual_review=False,
        )


def add_key_presses(a: TestAssignment, n: int):
    """Simulate n printable key presses (1 char each)."""
    base = timezone.now()
    for i in range(n):
        StudentActivityLog.objects.create(
            assignment=a,
            attempt_no=1,
            timestamp=base + timedelta(milliseconds=i * 120),
            event_type="key_press",
            pressed_key=random.choice("asdfghjkl"),
            chars_written=1,
        )


def add_gaze_offscreen(a: TestAssignment, seconds: int):
    """Each log adds ~2 s off-screen; seconds is approximate."""
    base = timezone.now()
    for i in range(seconds // 2):
        StudentActivityLog.objects.create(
            assignment=a,
            attempt_no=1,
            timestamp=base + timedelta(seconds=i * 2),
            event_type="gaze_offscreen",
            anomaly_score=0.4,
        )


def add_analysis_row(
    a: TestAssignment,
    *,
    esc=0,
    screen=0,
    tabs=0,
    blur=0,
    keys=0,
    delay=50,
    paste=0,
    focus=0,
    sus=False,
):
    StudentActivityAnalysis.objects.create(
        assignment=a,
        attempt_no=1,
        esc_pressed=esc,
        second_screen_events=screen,
        tab_switches=tabs,
        window_blurs=blur,
        total_key_presses=keys,
        average_key_delay=delay,
        copy_paste_events=paste,
        total_focus_lost=screen + blur + tabs,
        is_suspicious=sus,
    )


def add_audio(a: TestAssignment, ratio: float, mouth_open_no_voice: int):
    AudioAnalysis.objects.create(
        assignment=a,
        attempt_no=1,
        voiced_ratio=ratio,
        voiced_seconds=ratio * 90,
        mouth_open_no_voice_count=mouth_open_no_voice,
    )


# ----------  main routine ---------------------------------------------------

SCENARIOS = [
    # -----------------------------------------------------------------------
    # attachment test  (writing required)
    # -----------------------------------------------------------------------
    dict(
        student="neagu.ionut20@stud.ase.ro",
        test="attachment test",
        proctor=False,
        label=False,         # legit
        keys=500,
        offscreen=0,
        esc=0,
        screen=0,
        voiced=0.02,
        short=False,
    ),
    dict(
        student="neagu.ionut20@stud.ase.ro",
        test="attachment test",
        proctor=True,
        label=True,          # cheating
        keys=30,
        offscreen=80,
        esc=3,
        screen=3,
        voiced=0.6,
        short=True,
    ),
    # -----------------------------------------------------------------------
    # quiz (no writing required)
    # -----------------------------------------------------------------------
    dict(
        student="panaandreea20@stud.ase.ro",
        test="Quizz Test Database Sec (Training)",
        proctor=False,
        label=False,         # legit
        keys=0,
        offscreen=0,
        esc=0,
        screen=0,
        voiced=0.1,
        short=True,
    ),
    dict(
        student="panaandreea20@stud.ase.ro",
        test="Quizz Test Database Sec (Training)",
        proctor=True,
        label=True,          # cheating
        keys=0,
        offscreen=200,
        esc=2,
        screen=4,
        voiced=0.55,
        short=True,
    ),
]


def build_samples():
    for sc in SCENARIOS:
        student = User.objects.get(email=sc["student"])
        test = Test.objects.get(name=sc["test"])
        # ensure proctoring flag matches the scenario
        if test.use_proctoring != sc["proctor"]:
            test.use_proctoring = sc["proctor"]
            test.save(update_fields=["use_proctoring"])

        a = make_assignment(student, test, label=sc["label"])

        if sc["keys"]:
            add_key_presses(a, sc["keys"])

        if sc["offscreen"]:
            add_gaze_offscreen(a, sc["offscreen"])

        add_analysis_row(
            a,
            esc=sc["esc"],
            screen=sc["screen"],
            tabs=2 if sc["proctor"] else 0,
            keys=sc["keys"],
            paste=3 if sc["label"] else 0,
            sus=sc["label"],
        )
        add_audio(a, sc["voiced"], mouth_open_no_voice=1 if sc["label"] else 0)
        add_answers(a, short=sc["short"])

        # recompute aggregate keyboard metrics
        analyze_assignment_logs(a)

        print(f"✔︎ synthetic assignment {a.id} created for {student.email}")


if __name__ == "__main__":
    build_samples()
