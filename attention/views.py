from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
import cv2
import numpy as np
import base64
import mediapipe as mp
from .utils.pdf_report import render_attention_pdf
from .session_tracker import log_attention
from .ai_feedback import generate_ai_feedback, generate_realtime_feedback
from .session_tracker import get_session_stats, clear_session
from .models import AttentionReport
from django.conf import settings
from django.core.files import File
from pathlib import Path
from django.db import transaction
from threading import Thread

mp_face = mp.solutions.face_detection
face_detector = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def attention_check(request):
    frame_b64 = request.data.get("frame")
    session_id = request.data.get("session_id")

    if not frame_b64 or not session_id:
        return JsonResponse({"error": "Missing data"}, status=400)

    _, imgstr = frame_b64.split(";base64,")
    img_bytes = base64.b64decode(imgstr)
    img_np = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    h, w = img.shape[:2]

    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_detector.process(rgb)

    faces = []
    if results.detections:
        for det in results.detections:
            bbox = det.location_data.relative_bounding_box
            x1 = int(bbox.xmin * w)
            y1 = int(bbox.ymin * h)
            x2 = int((bbox.xmin + bbox.width) * w)
            y2 = int((bbox.ymin + bbox.height) * h)
            cx = (x1 + x2) // 2
            attentive = w * 0.25 < cx < w * 0.75

            faces.append({
                "x": x1,
                "y": y1,
                "w": x2 - x1,
                "h": y2 - y1,
                "attentive": attentive
            })

    log_attention(session_id, faces)
    return JsonResponse({"faces": faces})


def _bg_generate_report(session_id, user):

    professor = user.professor_profile

    raw = get_session_stats(session_id)
    clear_session(session_id)

    # timeline + avg
    timeline, ratios = [], []
    for idx,(ts,(att,total)) in enumerate(sorted(raw.items())):
        pct = 0 if total == 0 else att/total
        timeline.append({"timestamp": ts, "attention_pct": round(pct*100,1)})
        ratios.append(pct)
    avg = round(sum(ratios)/len(ratios)*100,1) if ratios else 0

    advice = generate_ai_feedback(timeline, avg)

    pdf_rel = render_attention_pdf(
        {
            "avg_attention": avg,
            "timeline": timeline,
            "advice": advice,
        },
        session_id=session_id,
    )

    # single-report, attach file once
    pdf_abs = Path(settings.MEDIA_ROOT) / pdf_rel
    report, created = AttentionReport.objects.get_or_create(
        session_id=session_id,
        defaults={
            "professor": professor,
            "created_by": user,
            "avg_attention": avg,
            "raw_timeline": timeline,
            "advice": advice,
        },
    )
    if created:
        with open(pdf_abs, "rb") as fh:
            report.pdf_file.save(pdf_rel.name, File(fh), save=True)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attention_end(request):
    session_id = request.data.get("session_id")
    user       = request.user

    if AttentionReport.objects.filter(session_id=session_id).exists():
        return JsonResponse({"detail": "Report already generated."})

    Thread(target=_bg_generate_report, args=(session_id, user), daemon=True).start()

    return JsonResponse({"detail": "Session received, report is processing."})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attention_feedback(request):
    session_id = request.data.get("session_id")
    if not session_id:
        return JsonResponse({"error": "Missing session_id"}, status=400)

    stats = get_session_stats(session_id)
    if not stats:
        return JsonResponse({"tip": "Not enough data yet."})

    # Calculate current average attention
    ratios = []
    for att, total in stats.values():
        if total > 0:
            ratios.append(att / total)
    avg = round(sum(ratios) / len(ratios) * 100, 1) if ratios else 0.0

    tip = generate_realtime_feedback(avg)
    return JsonResponse({"attention_avg": avg, "tip": tip})
