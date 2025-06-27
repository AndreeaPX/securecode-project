from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
import cv2
import numpy as np
import base64
import mediapipe as mp
from .utils.pdf_report import render_attention_pdf
from .session_tracker import log_attention, get_session_stats, clear_session
from .ai_feedback import generate_ai_feedback, generate_realtime_feedback
from .models import AttentionReport
from django.conf import settings
from django.core.files import File
from pathlib import Path
from threading import Thread
import contextlib, os, sys


mp_face = mp.solutions.face_detection
MODEL_SELECTION = 1        
MIN_CONF        = 0.2
SCALES          = (1.0, 2.0, 3.0)
NMS_IOU_THRESH  = 0.4       #If two boxes overlap >= 40 %, keep the biggest, drop the rest


@contextlib.contextmanager
def _suppress_mediapipe_logs():
    devnull = open(os.devnull, 'w')
    old = os.dup(2)
    os.dup2(devnull.fileno(), 2)
    try:
        yield
    finally:
        os.dup2(old, 2)
        devnull.close()


def _apply_clahe(rgb):
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)  #'LAB de-mixes them into Lightness and two chroma channels (A = green-↔-magenta, B = blue-↔-yellow).'
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(2.0, (8, 8)).apply(l)  #Contrast-Limited Adaptive Histogram Equalization
    #Classic histogram equalization can blow out noise; adaptive means it works on small 8×8 tiles so local dark zones get lifted without over-brightening everything.
    #Clip limit 2.0 guards against converting every subtle shadow into pure black/white.


    #Merge the boosted L back with the untouched A and B.
    #Convert back to RGB so the rest of the pipeline (and MediaPipe) understands it.
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2RGB)


def _adjust_gamma(rgb, gamma):
    lut = (np.arange(256) / 255.0) ** (1.0 / gamma) * 255
    return cv2.LUT(rgb, lut.astype("uint8"))


def _enhance_if_dark(rgb):
    if np.mean(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)) < 80:
        rgb = _apply_clahe(rgb)
        rgb = _adjust_gamma(rgb, 1.5)
    return rgb


def _is_looking_forward(det):
    try:
        kps = det.location_data.relative_keypoints
        right_eye, left_eye, nose = kps[0], kps[1], kps[2]
        eye_cx = (right_eye.x + left_eye.x) / 2.0
        return abs(nose.x - eye_cx) < 0.02  #2 percent -- can be improved
    except Exception:
        return False


def _iou(boxA, boxB):
    xA = max(boxA[0], boxB[0]); yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2]); yB = min(boxA[3], boxB[3])
    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    inter = interW * interH
    if inter == 0:
        return 0.0
    areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    return inter / (areaA + areaB - inter)


def _nms(boxes, atts, thr=NMS_IOU_THRESH):
    if not boxes:
        return [], []
    idxs = sorted(range(len(boxes)), key=lambda i: (boxes[i][2]-boxes[i][0])*(boxes[i][3]-boxes[i][1]), reverse=True)
    keep = []
    while idxs:
        cur = idxs.pop(0)
        keep.append(cur)
        idxs = [i for i in idxs if _iou(boxes[cur], boxes[i]) < thr]
    return [boxes[i] for i in keep], [atts[i] for i in keep]


def _detect_faces(rgb, h, w):
    boxes, atts = [], []
    for scale in SCALES:
        img = rgb if scale == 1.0 else cv2.resize(rgb, None, fx=scale, fy=scale)
        with _suppress_mediapipe_logs():
            det_obj = mp_face.FaceDetection(model_selection=MODEL_SELECTION, min_detection_confidence=MIN_CONF)
            res = det_obj.process(img)
            det_obj.close()
        if not res.detections:
            continue
        for det in res.detections:
            bbox = det.location_data.relative_bounding_box
            x1 = int(bbox.xmin * w); y1 = int(bbox.ymin * h)
            x2 = int((bbox.xmin + bbox.width) * w)
            y2 = int((bbox.ymin + bbox.height) * h)
            boxes.append([max(x1,0), max(y1,0), min(x2,w-1), min(y2,h-1)])
            atts.append(_is_looking_forward(det))

    boxes, atts = _nms(boxes, atts)

    faces = []
    for (x1, y1, x2, y2), att in zip(boxes, atts):
        faces.append({
            "x": x1,
            "y": y1,
            "w": x2 - x1,
            "h": y2 - y1,
            "attentive": att,
        })
    return faces


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attention_check(request):
    frame_b64 = request.data.get("frame"); session_id = request.data.get("session_id")
    if not frame_b64 or not session_id:
        return JsonResponse({"error": "Missing data"}, status=400)
    try:
        _, enc = frame_b64.split(";base64,")
        img = cv2.imdecode(np.frombuffer(base64.b64decode(enc), np.uint8), cv2.IMREAD_COLOR)
    except Exception:
        return JsonResponse({"error": "Bad image data"}, status=400)
    if img is None:
        return JsonResponse({"error": "Invalid image"}, status=400)

    h, w = img.shape[:2]
    rgb = _enhance_if_dark(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    faces = _detect_faces(rgb, h, w)
    log_attention(session_id, faces)
    return JsonResponse({"faces": faces})


def _bg_generate_report(session_id, user):
    professor = user.professor_profile
    raw = get_session_stats(session_id); clear_session(session_id)
    timeline, ratios = [], []
    att_sum = 0
    total_sum = 0
    for ts, (att, total) in sorted(raw.items()):
        pct = 0 if total == 0 else att/total
        att_sum +=att
        total_sum +=total
        timeline.append({"timestamp": ts, "attention_pct": round(pct*100,1)})
        ratios.append(pct)
    avg = round(att_sum / total_sum * 100, 1) if total_sum else 0.0
    try:
        advice = generate_ai_feedback(timeline, avg)
    except Exception as e:
        advice = f"AI feedback unavailable: {str(e).splitlines()[0]}"
    if not timeline:
        advice = "No faces detected. Verify camera coverage."
    pdf_rel = render_attention_pdf({"avg_attention": avg, "timeline": timeline, "advice": advice}, session_id=session_id)
    pdf_abs = Path(settings.MEDIA_ROOT)/pdf_rel
    rep,_ = AttentionReport.objects.get_or_create(session_id=session_id, defaults={"professor": professor,"created_by": user,"avg_attention": avg,"raw_timeline": timeline,"advice": advice})
    if not rep.pdf_file:
        with open(pdf_abs,"rb") as fh: rep.pdf_file.save(pdf_rel.name, File(fh), save=True)

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attention_end(request):
    sid = request.data.get("session_id"); user = request.user
    if AttentionReport.objects.filter(session_id=sid).exists():
        return JsonResponse({"detail": "Report already generated."})
    Thread(target=_bg_generate_report, args=(sid, user), daemon=True).start()
    return JsonResponse({"detail": "Session received, report is processing."})

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def attention_feedback(request):
    sid = request.data.get("session_id")
    if not sid:
        return JsonResponse({"error": "Missing session_id"}, status=400)
    stats = get_session_stats(sid)
    if not stats:
        return JsonResponse({"tip": "Not enough data yet."})
    ratios = [att/total for att,total in stats.values() if total]
    avg = round(np.mean(ratios)*100,1) if ratios else 0.0
    tip = generate_realtime_feedback(avg)
    return JsonResponse({"attention_avg": avg, "tip": tip})
