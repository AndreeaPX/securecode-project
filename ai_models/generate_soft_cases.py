import random
from users.models import StudentActivityAnalysis, AudioAnalysis, StudentActivityLog, TestAssignment
from django.utils import timezone

def create_soft_cheating_case(assignment, attempt_no):
    saa, _ = StudentActivityAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    saa.esc_pressed = random.choice([1, 2])  # borderline
    saa.second_screen_events = random.choice([1, 2])
    saa.tab_switches = random.choice([1, 2])
    saa.window_blurs = random.choice([1, 2])
    saa.copy_paste_events = random.choice([1, 2])
    saa.total_key_presses = random.randint(30, 60)
    saa.average_key_delay = random.uniform(25.0, 40.0)
    saa.total_focus_lost = random.choice([0, 1])
    saa.save()

    aa, _ = AudioAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    aa.voiced_ratio = random.uniform(0.25, 0.45)
    aa.voiced_seconds = random.uniform(5, 15)
    aa.mouth_open_no_voice_count = random.randint(0, 2)
    aa.save()

    # face events that don't scream cheating
    if random.random() < 0.3:
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=attempt_no,
            timestamp=timezone.now(),
            event_type="face_mismatch",
            event_message="Face slightly off-angle",
            anomaly_score=0.4,
            focus_lost_count=1
        )


def create_noisy_legit_case(assignment, attempt_no):
    saa, _ = StudentActivityAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    saa.esc_pressed = random.choice([0, 1])
    saa.second_screen_events = 0
    saa.tab_switches = random.choice([0, 1])
    saa.window_blurs = random.choice([0, 2])
    saa.copy_paste_events = 0
    saa.total_key_presses = random.randint(250, 400)
    saa.average_key_delay = random.uniform(15.0, 30.0)
    saa.total_focus_lost = random.choice([0, 1])
    saa.save()

    aa, _ = AudioAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    aa.voiced_ratio = random.uniform(0.02, 0.1)  # appears silent
    aa.voiced_seconds = random.uniform(2, 5)
    aa.mouth_open_no_voice_count = 0
    aa.save()

    # Random, but not alarming
    if random.random() < 0.2:
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=attempt_no,
            timestamp=timezone.now(),
            event_type="no_face_found",
            event_message="Temporary camera glitch",
            anomaly_score=0.2
        )

def create_edge_legit_case(assignment, attempt_no):
    saa, _ = StudentActivityAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    saa.esc_pressed = 0
    saa.second_screen_events = 0
    saa.tab_switches = 1
    saa.window_blurs = 5  # pare nevinovat
    saa.copy_paste_events = 0
    saa.total_key_presses = 300
    saa.average_key_delay = 45.0
    saa.total_focus_lost = 0
    saa.save()

    aa, _ = AudioAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    aa.voiced_ratio = 0.6  # prea multă voce?
    aa.voiced_seconds = 60
    aa.mouth_open_no_voice_count = 3
    aa.save()

    StudentActivityLog.objects.create(
        assignment=assignment,
        attempt_no=attempt_no,
        timestamp=timezone.now(),
        event_type="voice_detected",
        event_message="Constant murmuring",
        anomaly_score=0.5
    )


def create_ai_confusing_case(assignment, attempt_no):
    saa, _ = StudentActivityAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    saa.esc_pressed = 2
    saa.second_screen_events = 1
    saa.tab_switches = 0
    saa.window_blurs = 0
    saa.copy_paste_events = 6
    saa.total_key_presses = 25
    saa.average_key_delay = 8.0
    saa.total_focus_lost = 0
    saa.save()

    # No audio at all
    AudioAnalysis.objects.filter(assignment=assignment, attempt_no=attempt_no).delete()

    StudentActivityLog.objects.create(
        assignment=assignment,
        attempt_no=attempt_no,
        timestamp=timezone.now(),
        event_type="face_mismatch",
        event_message="Low light, unclear face",
        anomaly_score=0.3
    )


def legit_with_high_voice(assignment, attempt_no):
    saa, _ = StudentActivityAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    saa.esc_pressed = 0
    saa.second_screen_events = 0
    saa.tab_switches = 0
    saa.window_blurs = 0
    saa.copy_paste_events = 0
    saa.total_key_presses = 250
    saa.average_key_delay = 25.0
    saa.total_focus_lost = 0
    saa.save()

    aa, _ = AudioAnalysis.objects.get_or_create(assignment=assignment, attempt_no=attempt_no)
    aa.voiced_ratio = 0.65  # ridicat, dar e în background
    aa.voiced_seconds = 50
    aa.mouth_open_no_voice_count = 0  # deci studentul nu vorbea
    aa.save()

    print(f"Injected noisy legit case (voiced_ratio only) for assignment {assignment.id}")


def run_generator():
    test = TestAssignment.objects.filter(test__name__icontains="Mega Test").first().test
    assignments = TestAssignment.objects.filter(test=test)
    for i, a in enumerate(assignments):
        if i % 5 == 0:
            create_soft_cheating_case(a, a.attempt_no)
        elif i % 5 == 1:
            create_noisy_legit_case(a, a.attempt_no)
        elif i % 5 == 2:
            create_edge_legit_case(a, a.attempt_no)
        elif i % 5 == 3:
            create_ai_confusing_case(a, a.attempt_no)
        elif i%5==4:
            legit_with_high_voice(a, a.attempt_no)
        else:
            create_soft_cheating_case(a, a.attempt_no)
    print("✅ Soft cases generated.")

