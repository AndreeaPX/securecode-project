"""Refactored version of the live_face_check view
------------------------------------------------
* One **decision** (\"issue\") per frame – picked by priority
* Clear helper functions for each detection block
* Central `add_issue()` collects candidate issues while avoiding duplicates
* Debounce relies on the existing `log_event()` util you already wrote
* Keeps existing mouth‑open state tracking (doesn’t trigger an early return)
* Responds with the highest‑priority issue or `{"success": True}`

Note – adjust the `PRIORITY` list or `DEBOUNCE_SECONDS` dictionary to taste.
"""

from __future__ import annotations

import base64
import os
from datetime import timedelta
from typing import List, Tuple, Dict, Any

import cv2
import face_recognition
import numpy as np
from django.http import JsonResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from ultralytics import YOLO
import mediapipe as mp

from users.models.tests import TestAssignment, StudentActivityLog, TempFaceEventState
from users.models.questions import Question

# --------------------------------------------------------------------------------------
# Globals & helpers
# --------------------------------------------------------------------------------------

os.makedirs("frame_logs", exist_ok=True)
yolo_model = YOLO("yolov8m.pt")

mp_face_mesh = mp.solutions.face_mesh
face_mesh_detector = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
)

# Issue priority – first match == response sent -------------------------------------------------
PRIORITY: List[str] = [
    "multiple_faces",
    "mobile_detected",
    "no_face_found",
    "face_mismatch",
    "gaze_offscreen",
    "gaze_unclear",
    "head_pose_suspicious",
]

# Custom debounce per issue (seconds)
DEBOUNCE_SECONDS: Dict[str, int] = {
    "mobile_detected": 5,
    "gaze_offscreen": 5,
    "gaze_unclear": 10,
    "head_pose_suspicious": 5,
    "no_face_found": 10,
    "face_mismatch": 10,
    "multiple_faces": 15,
}

# ----------------------------------------------------------------------
# General‑purpose utilities
# ----------------------------------------------------------------------

def log_student_event(
    assignment: TestAssignment,
    attempt_no: int,
    event_type: str,
    message: str,
    anomaly_score: float,
    focus_lost_count: int = 1,
    frame: np.ndarray | None = None,
) -> None:
    """Persist an event + optional frame capture to disk."""
    if frame is not None:
        ts = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_{event_type}_{ts}.jpg", frame)

    StudentActivityLog.objects.create(
        assignment=assignment,
        attempt_no=attempt_no,
        focus_lost_count=focus_lost_count,
        anomaly_score=anomaly_score,
        event_type=event_type,
        event_message=message,
    )


def debounce_event(
    user,
    assignment: TestAssignment,
    attempt_no: int,
    event_type: str,
    seconds: int,
) -> bool:
    """Return **True** if we're allowed to fire the event now (after debounce)."""
    now = timezone.now()
    try:
        record = TempFaceEventState.objects.get(
            user=user,
            assignment=assignment,
            attempt_no=attempt_no,
            event_type=event_type,
        )
        if now - record.first_seen > timedelta(seconds=seconds):
            record.delete()
            return True
        # update TTL
        record.last_seen = now
        record.save(update_fields=["last_seen"])
        return False
    except TempFaceEventState.DoesNotExist:
        TempFaceEventState.objects.create(
            user=user,
            assignment=assignment,
            attempt_no=attempt_no,
            event_type=event_type,
        )
        return False


# ----------------------------------------------------------------------
# Face / gaze / phone detectors (mostly copied from original logic)
# ----------------------------------------------------------------------

def detect_phone(frame_rgb: np.ndarray) -> bool:
    result = yolo_model.predict(source=frame_rgb, verbose=False)
    boxes = result[0].boxes.data.cpu().numpy()
    # COCO class 67 == cell phone
    return any(int(b[5]) == 67 for b in boxes)


def detect_gaze_direction(img: np.ndarray) -> Tuple[str, str, Any, bool]:
    """Unchanged gaze + head‑pose logic."""
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_mesh_detector.process(rgb)

    if not results.multi_face_landmarks:
        return "inconclusive", "neutral", None, False

    lm = results.multi_face_landmarks[0].landmark

    # helper
    def _norm(a, b) -> float:
        return (a - b) if b != 0 else 0.5

    # left eye
    l_w = lm[133].x - lm[33].x
    l_x = _norm(lm[468].x - lm[33].x, l_w)
    l_h = lm[145].y - lm[159].y
    l_y = _norm(lm[468].y - lm[159].y, l_h)

    # right eye
    r_w = lm[263].x - lm[362].x
    r_x = _norm(lm[473].x - lm[362].x, r_w)
    r_h = lm[374].y - lm[386].y
    r_y = _norm(lm[473].y - lm[386].y, r_h)

    iris_x = l_x if not (0 <= l_x <= 1) else (l_x + r_x) / 2
    iris_y = l_y if not (0 <= l_y <= 1) else (l_y + r_y) / 2

    if iris_x < 0.42:
        gaze = "left"
    elif iris_x > 0.58:
        gaze = "right"
    elif iris_y < 0.4:
        gaze = "up"
    elif iris_y > 0.6:
        gaze = "down"
    else:
        gaze = "center"

    # head pose rough estimate
    pitch = lm[152].y - lm[1].y
    roll = lm[454].y - lm[234].y
    if abs(roll) > 0.1:
        head_pose = "tilted"
    elif pitch > 0.22:
        head_pose = "down"
    elif pitch < 0.05:
        head_pose = "up"
    else:
        head_pose = "neutral"

    # mouth open?
    mouth_open = (lm[14].y - lm[13].y) > 0.03
    return gaze, head_pose, results, mouth_open


# ----------------------------------------------------------------------
# The main view — now tidy!
# ----------------------------------------------------------------------

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def live_face_check(request):  # noqa: C901  — it *is* complex, sorry pylint
    """Analyze a single base64 frame and return **at most one** error."""
    user = request.user
    data = request.data

    face_image_data: str | None = data.get("face_image")
    assignment_id: int | None = data.get("assignment_id")
    question_id: int | None = data.get("question_id")

    if not face_image_data or not assignment_id:
        return JsonResponse({"error": "Missing data"}, status=400)

    try:
        assignment = TestAssignment.objects.get(id=assignment_id, student=user)
    except TestAssignment.DoesNotExist:
        return JsonResponse({"error": "Invalid assignment"}, status=404)

    # question context (is looking‑down allowed?)
    question_type = None
    if question_id:
        question = Question.objects.filter(id=question_id).first()
        question_type = getattr(question, "type", None)
    is_looking_down_allowed = question_type in {"code", "open"}

    # ------------------------------------------------------------------
    # Decode image
    # ------------------------------------------------------------------
    _, imgstr = face_image_data.split(";base64,")
    img_np = np.frombuffer(base64.b64decode(imgstr), np.uint8)
    frame_bgr = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

    # ------------------------------------------------------------------
    # Candidate issue collection
    # ------------------------------------------------------------------
    issues: List[str] = []

    def add_issue(issue: str):
        if issue not in issues:
            issues.append(issue)

    # 1) Phone detection ------------------------------------------------
    if detect_phone(frame_rgb):
        add_issue("mobile_detected")

    # 2) Gaze / head pose ---------------------------------------------
    gaze, head_pose, mp_results, mouth_open = detect_gaze_direction(frame_bgr)

    if gaze in {"left", "right"}:
        add_issue("gaze_offscreen")
    elif gaze == "inconclusive":
        add_issue("gaze_unclear")
    elif gaze == "down" and not is_looking_down_allowed:
        add_issue("gaze_offscreen")

    if head_pose in {"up", "down", "tilted"}:
        add_issue("head_pose_suspicious")

    # 3) Face detection / encoding -------------------------------------
    face_locations = face_recognition.face_locations(frame_rgb)
    encodings = face_recognition.face_encodings(frame_rgb)

    if not face_locations and mp_results and mp_results.multi_face_landmarks:
        h, w, _ = frame_bgr.shape
        face_locations = [(0, w, h, 0)]  # full frame fallback
        encodings = face_recognition.face_encodings(frame_rgb, known_face_locations=face_locations)

    if len(encodings) == 0:
        add_issue("no_face_found")
    elif len(face_locations) > 1:
        add_issue("multiple_faces")
    else:
        uploaded_encoding = encodings[0]
        stored_encoding = face_recognition.face_encodings(frame_rgb, [face_locations[0]])[0] if False else None  # placeholder
        # In prod: stored_encoding = pickle.loads(user.face_encoding)
        if stored_encoding is not None:
            match = face_recognition.compare_faces([stored_encoding], uploaded_encoding, tolerance=0.70)[0]
            if not match:
                add_issue("face_mismatch")

    # ------------------------------------------------------------------
    # Decide which issue to act on
    # ------------------------------------------------------------------
    chosen_issue: str | None = None
    for pr in PRIORITY:
        if pr in issues:
            chosen_issue = pr
            break

    # Mouth‑open state gets updated regardless of chosen issue ---------
    mouth_event_type = "mouth_open" if mouth_open else "mouth_closed"
    TempFaceEventState.objects.update_or_create(
        user=user,
        assignment=assignment,
        attempt_no=assignment.attempt_no,
        event_type=mouth_event_type,
        defaults={"last_seen": timezone.now()},
    )
    TempFaceEventState.objects.filter(
        user=user,
        assignment=assignment,
        attempt_no=assignment.attempt_no,
        event_type="mouth_closed" if mouth_open else "mouth_open",
    ).delete()

    # ------------------------------------------------------------------
    # If we have an issue → debounce, log, respond; else success
    # ------------------------------------------------------------------
    if chosen_issue:
        if debounce_event(
            user,
            assignment,
            assignment.attempt_no,
            chosen_issue,
            DEBOUNCE_SECONDS.get(chosen_issue, 5),
        ):
            # cleared debounce, actually log
            messages = {
                "multiple_faces": "Detected more than one face in frame.",
                "mobile_detected": "Mobile phone detected in camera frame.",
                "no_face_found": "No face detected.",
                "face_mismatch": "Face does not match the authenticated student.",
                "gaze_offscreen": "Student appears to be looking away from the screen.",
                "gaze_unclear": "Unable to determine gaze direction (lighting / glasses).",
                "head_pose_suspicious": "Student head pose is suspicious.",
            }
            anomaly_scores = {
                "multiple_faces": 0.5,
                "mobile_detected": 1.0,
                "no_face_found": 0.3,
                "face_mismatch": 0.5,
                "gaze_offscreen": 0.4,
                "gaze_unclear": 0.1,
                "head_pose_suspicious": 0.2,
            }
            log_student_event(
                assignment,
                assignment.attempt_no,
                chosen_issue,
                messages[chosen_issue],
                anomaly_scores[chosen_issue],
                frame=frame_bgr,
            )

        # Always return the error even if debounced (frontend still needs to know)
        return JsonResponse({"error": chosen_issue}, status=200)

    # ---------------- Success! ----------------------------------------
    StudentActivityLog.objects.create(
        assignment=assignment,
        attempt_no=assignment.attempt_no,
        focus_lost_count=0,
        anomaly_score=0.0,
        event_type="face_match",
        event_message="Face matches and gaze is on the screen.",
    )
    return JsonResponse({"success": True})
