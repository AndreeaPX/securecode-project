exec("""
from users.models.tests import TestAssignment
from ai_models.features import extract_features_for_assignment
from users.views.mouse_keyboard_view import analyze_assignment_logs
from django.contrib.auth import get_user_model
from pprint import pprint

STUDENTS = [
    "neagu.ionut20@stud.ase.ro",
    "panaandreea20@stud.ase.ro",
]

TESTS = {
    "proctoring grila": range(1, 11),
    "proctoring scris": range(1, 11),
}

User = get_user_model()
grand_total = 0
missing = []

for email in STUDENTS:
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        print(f"⚠️  No such user: {email}")
        continue

    for test_name, attempts in TESTS.items():
        for attempt_no in attempts:
            qs = TestAssignment.objects.filter(
                student=user,
                test__name=test_name,
                attempt_no=attempt_no,
            )
            if not qs.exists():
                missing.append((email, test_name, attempt_no))
                continue

            a = qs.first()
            analyze_assignment_logs(a)
            features_dict = extract_features_for_assignment(a)

            print("\\n" + "-" * 80)
            print(f"📄  {email} | {test_name} | Attempt {attempt_no} | Assignment #{a.id}")
            print("-" * 80)
            print("• High-level (distilled) features:")
            pprint(features_dict["features"], width=100)
            print("\\n• Raw counters:")
            pprint(features_dict["raw"], width=100)

            grand_total += 1

print(f"\\n✅  Extracted features for {grand_total} assignments.")

if missing:
    print("\\n⚠️  Assignments not found (did they run / label yet?)")
    for tup in missing:
        print("   ", tup)
""")
