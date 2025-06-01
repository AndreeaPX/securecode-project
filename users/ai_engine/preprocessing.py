from users.models.tests import StudentActivityLog
from django.utils import timezone

def get_lstm_sequence(assignment, window_size=10):
    logs = StudentActivityLog.objects.filter(
        assignment=assignment
    ).order_by("timestamp")

    if not logs.exists():
        return []

    start_time = logs.first().timestamp
    end_time = logs.last().timestamp
    total_seconds = int((end_time - start_time).total_seconds())
    num_windows = max(1, total_seconds // window_size + 1)

    sequence = []

    for i in range(num_windows):
        window_start = start_time + timezone.timedelta(seconds=i * window_size)
        window_end = window_start + timezone.timedelta(seconds=window_size)

        step_logs = logs.filter(timestamp__gte=window_start, timestamp__lt=window_end)

        def has_event(event_type):
            return step_logs.filter(event_type=event_type).exists()

        typing_delays = list(
            step_logs.filter(event_type="key_press")
            .values_list("key_delay", flat=True)
        )
        typing_delays = [d for d in typing_delays if d is not None]

        key_presses = step_logs.filter(event_type="key_press")
        copy_paste_events = step_logs.filter(event_type__in=["copy_event", "paste_event", "cut_event"])
        esc_presses = step_logs.filter(event_type="esc_pressed")

        # 🔧 Fix aici
        scores = [log.anomaly_score for log in step_logs if log.anomaly_score is not None]
        anomaly_avg = sum(scores) / len(scores) if scores else 0.0

        timestep = [
            int(has_event("gaze_offscreen")),                
            int(has_event("head_pose_suspicious")),          
            int(has_event("face_mismatch")),                 
            int(has_event("no_face_found")),                 
            int(has_event("mobile_detected")),               
            int(
                has_event("window_blur") or
                has_event("tab_hidden") or
                has_event("second_screen")
            ),                                               
            int(key_presses.exists()),                       
            sum(typing_delays) / len(typing_delays) if typing_delays else 0.0,
            key_presses.count(),                             
            copy_paste_events.count(),                       
            esc_presses.count(),                             
            sum(typing_delays) / len(typing_delays) if typing_delays else 0.0,  
            anomaly_avg                                      
        ]

        sequence.append(timestep)

    return sequence
