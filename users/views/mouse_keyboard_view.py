from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from users.models.tests import TestAssignment, StudentActivityLog
from users.models.tests import StudentActivityAnalysis 
import json

def analyze_assignment_logs(assignment):
    logs = StudentActivityLog.objects.filter(assignment=assignment, attempt_no=assignment.attempt_no)
    esc = logs.filter(event_type="esc_pressed").count()
    second_screen = logs.filter(event_type="second_screen").count()
    tab_switches = logs.filter(event_type="tab_hidden").count()
    window_blurs = logs.filter(event_type="window_blur").count()
    copy_paste = logs.filter(event_type__in=["copy_event", "paste_event", "cut_event"]).count()/2
    key_presses = logs.filter(event_type="key_press").count()

    delays = logs.filter(event_type="key_press").values_list("key_delay", flat=True)
    delays = [d for d in delays if d is not None]
    avg_delay = sum(delays) / len(delays) if delays else None

    if assignment.test.use_proctoring:
        is_sus = (
            esc > 2 or
            second_screen > 2 or
            tab_switches > 2 or
            window_blurs > 2 or
            (avg_delay is not None and avg_delay < 50)
        )
    else:
        is_sus = False

    analysis, _ = StudentActivityAnalysis.objects.update_or_create(
        assignment=assignment,
        attempt_no=assignment.attempt_no,
        defaults={
            "esc_pressed": esc,
            "second_screen_events": second_screen,
            "tab_switches": tab_switches,
            "window_blurs": window_blurs,
            "total_key_presses": key_presses,
            "average_key_delay": avg_delay,
            "copy_paste_events": copy_paste,
            "total_focus_lost": second_screen + window_blurs + tab_switches,
            "is_suspicious": is_sus
        }
    )

    return analysis

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def mouse_keyboard_check(request):
    user = request.user
    data = request.data

    assignment_id = data.get("assignment_id")
    event_type = data.get("event_type")
    event_message = data.get("event_message", "")
    anomaly_score = data.get("anomaly_score", 0.1)

    if not assignment_id or not event_type:
        return Response({"error": "Missing required fields."}, status=400)

    try:
        assignment = TestAssignment.objects.get(id=assignment_id, student=user)
    except TestAssignment.DoesNotExist:
        return Response({"error": "Invalid assignment ID or unauthorized."}, status=403)

    key = None
    delay = None
    if event_type == "key_press":
        try:
            msg = json.loads(event_message)
            key = msg.get("key")
            delay = msg.get("time_since_last")
        except:
            pass

    StudentActivityLog.objects.create(
        assignment=assignment,
        attempt_no=assignment.attempt_no+1,
        timestamp=timezone.now(),
        event_type=event_type,
        event_message=event_message,
        anomaly_score=anomaly_score,
        pressed_key=key,
        key_delay=delay,
        focus_lost_count=1 if event_type in ["window_blur", "tab_hidden", "second_screen"] else 0
    )

    return Response({"success": True})
