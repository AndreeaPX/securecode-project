from __future__ import annotations
from django.db import models


from datetime import timedelta, datetime
import random
from typing import Sequence

from django.utils import timezone
from django.db import transaction

from users.models.tests import (
    TestAssignment,
    StudentActivityLog,
    StudentActivityAnalysis,
    AudioAnalysis,
    StudentAnswer,
    Test,
)
from users.models.core import User
from users.models.questions import Question

# ---------------------------------------------------------------------------
# helper utilities -----------------------------------------------------------
# ---------------------------------------------------------------------------

_CAM_CHEAT_EVENTS: Sequence[str] = (
    "mobile_detected",
    "face_mismatch",
    "multiple_faces",
    "no_face_found",
)

_CAM_LEGIT_EVENTS: Sequence[str] = (
    "gaze_offscreen",
    "head_pose_suspicious",
)

_KEY_ALPHABET = "abcdefghijklmnopqrstuvwxyz"


# ---------------------------------------------------------------------------
# main entry -----------------------------------------------------------------
# ---------------------------------------------------------------------------

def _rand_key() -> str:
    return random.choice(_KEY_ALPHABET)

def _now() -> datetime:
    # one point in time, we use +n seconds for subsequent events
    return timezone.now()


def _insert_log(
    *,
    assignment: TestAssignment,
    event_type: str,
    secs_offset: int = 0,
    anomaly: float = 0.1,
    focus_loss: bool = False,
    pressed_key: str | None = None,
    chars_written: int = 0,
    key_delay: float | None = None,
) -> None:
    StudentActivityLog.objects.create(
        assignment=assignment,
        attempt_no=assignment.attempt_no,
        timestamp=_now() + timedelta(seconds=secs_offset),
        event_type=event_type,
        event_message="synthetic",  # keep it simple
        anomaly_score=anomaly,
        focus_lost_count=1 if focus_loss else 0,
        pressed_key=pressed_key,
        chars_written=chars_written,
        key_delay=key_delay,
    )


def _add_keyboard_sequence(assignment: TestAssignment, n_chars: int) -> None:
    """Insert *n_chars* key_press events with plausible 90–250 ms gaps."""
    delay_ms = 90
    for i in range(n_chars):
        key = _rand_key()
        _insert_log(
            assignment=assignment,
            event_type="key_press",
            secs_offset=i * delay_ms / 1000,
            anomaly=0.05,
            pressed_key=key,
            chars_written=1,
            key_delay=delay_ms,
        )
        delay_ms = random.randint(90, 250)


def _aggregate_analysis(assignment: TestAssignment) -> None:
    """Create/update the StudentActivityAnalysis row from raw logs."""
    logs = StudentActivityLog.objects.filter(
        assignment=assignment, attempt_no=assignment.attempt_no
    )

    esc = logs.filter(event_type="esc_pressed").count()
    second_screen = logs.filter(event_type="second_screen").count()
    tab_switches = logs.filter(event_type="tab_hidden").count()
    window_blurs = logs.filter(event_type="window_blur").count()
    copy_paste = (
        logs.filter(event_type__in=["copy_event", "paste_event", "cut_event"]).count() // 2
    )
    key_presses = logs.filter(event_type="key_press").count()
    total_chars = logs.aggregate(total=models.Sum("chars_written"))[
        "total"
    ] or 0
    delays = list(logs.filter(event_type="key_press").values_list("key_delay", flat=True))
    delays = [d for d in delays if d is not None]
    avg_delay = sum(delays) / len(delays) if delays else None

    StudentActivityAnalysis.objects.update_or_create(
        assignment=assignment,
        attempt_no=assignment.attempt_no,
        defaults=dict(
            esc_pressed=esc,
            second_screen_events=second_screen,
            tab_switches=tab_switches,
            window_blurs=window_blurs,
            copy_paste_events=copy_paste,
            total_key_presses=key_presses,
            average_key_delay=avg_delay,
            total_focus_lost=second_screen + window_blurs + tab_switches,
            is_suspicious=False,  # let the model decide later
            total_chars=total_chars,
        ),
    )


def _add_answers(assignment: TestAssignment, short: bool) -> None:
    """Insert dummy answers so *total_chars* can be computed later if needed."""
    qs = Question.objects.filter(testquestion__test=assignment.test)
    for q in qs:
        StudentAnswer.objects.create(
            assignment=assignment,
            question=q,
            answer_text="x" * (80 if short else 500),
            needs_manual_review=False,
        )


@transaction.atomic
def _single_assignment(
    *,
    student: User,
    test: Test,
    label_cheating: bool,
    is_quiz: bool,
    idx: int,
) -> None:
    """Generate *one* assignment + logs according to the scenario."""
    a = TestAssignment.objects.create(
        student=student,
        test=test,
        started_at=_now(),
        finished_at=_now() + timedelta(minutes=10),
        attempt_no=1,
        label=label_cheating,
    )

    # ---------------------------------------------------------------------
    # quiz ⇒ 0 key‑presses, written ⇒ realistic typing
    # ---------------------------------------------------------------------
    if not is_quiz:
        n_chars = random.randint(400, 900)
        _add_keyboard_sequence(a, n_chars)
    else:
        # Key‑presses should be *absent* in quiz mode.
        pass

    # ---------------------------------------------------------------------
    # camera & focus / cheating vs legit
    # ---------------------------------------------------------------------
    if label_cheating:
        # heavy & obvious cheating
        bad_events = random.sample(_CAM_CHEAT_EVENTS, k=2)
        for ev in bad_events:
            _insert_log(assignment=a, event_type=ev, anomaly=0.9, focus_loss=True)
        # additional ESC / second‑screen to trigger proctoring rule
        _insert_log(assignment=a, event_type="esc_pressed", anomaly=0.8)
        _insert_log(assignment=a, event_type="esc_pressed", anomaly=0.8, secs_offset=2)
        _insert_log(assignment=a, event_type="second_screen", anomaly=0.8, focus_loss=True)
    else:
        # mostly clean, mild distractions
        ev = random.choice(_CAM_LEGIT_EVENTS)
        _insert_log(assignment=a, event_type=ev, anomaly=0.2, focus_loss=False)

    # ---------------------------------------------------------------------
    # simulate one tab_hidden (allowed once before kick)
    # ---------------------------------------------------------------------
    if test.use_proctoring:
        _insert_log(assignment=a, event_type="tab_hidden", anomaly=0.4, focus_loss=True)

    # ---------------------------------------------------------------------
    # answers & analysis row ------------------------------------------------
    # ---------------------------------------------------------------------
    _add_answers(a, short=is_quiz)
    _aggregate_analysis(a)

    if test.has_ai_assistent and test.allow_sound_analysis:
        # create a dummy AudioAnalysis so features don't blow up
        AudioAnalysis.objects.get_or_create(
            assignment=a,
            attempt_no=1,
            defaults=dict(voiced_ratio=0.02, voiced_seconds=1.2, mouth_open_no_voice_count=0),
        )


# ---------------------------------------------------------------------------
# public helper --------------------------------------------------------------
# ---------------------------------------------------------------------------

def generate_samples(
    *,
    student_email: str,
    quiz_test_name: str,
    written_student_email: str,
    written_test_name: str,
    num_per_type: int = 10,
) -> None:
    """Entry‑point used from Django shell."""

    student_quiz = User.objects.get(email=student_email)
    student_written = User.objects.get(email=written_student_email)

    quiz_test = Test.objects.get(name=quiz_test_name)
    written_test = Test.objects.get(name=written_test_name)

    # clean previous synthetic attempts for the two students / tests only
    TestAssignment.objects.filter(
        student__in=[student_quiz, student_written],
        test__in=[quiz_test, written_test],
    ).delete()

    # quiz attempts --------------------------------------------------------
    for i in range(num_per_type):
        _single_assignment(
            student=student_quiz,
            test=quiz_test,
            label_cheating=False,
            is_quiz=True,
            idx=i,
        )
        _single_assignment(
            student=student_quiz,
            test=quiz_test,
            label_cheating=True,
            is_quiz=True,
            idx=i,
        )

    # written attempts -----------------------------------------------------
    for i in range(num_per_type):
        _single_assignment(
            student=student_written,
            test=written_test,
            label_cheating=False,
            is_quiz=False,
            idx=i,
        )
        _single_assignment(
            student=student_written,
            test=written_test,
            label_cheating=True,
            is_quiz=False,
            idx=i,
        )

    print(
        f"✅ Generated {num_per_type*4} synthetic assignments "
        f"({num_per_type*2} for each test – half legit, half cheating)."
    )
