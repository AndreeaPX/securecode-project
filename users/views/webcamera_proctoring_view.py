from users.models.tests import TestAssignment, StudentActivityLog
from users.models.questions import Question
import numpy as np
from ultralytics import YOLO
from django.utils import timezone
import os
import base64
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import cv2
import face_recognition
import pickle
import mediapipe as mp

os.makedirs("frame_logs", exist_ok=True)
yolo_model = YOLO("yolov8m.pt")

mp_face_mesh = mp.solutions.face_mesh
face_mesh_detector = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True
)

def detect_gaze_direction(img):
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = face_mesh_detector.process(rgb)

    if not results.multi_face_landmarks:
        return "inconclusive", "inconclusive"
    
    landmarks = results.multi_face_landmarks[0].landmark

    # --- LEFT EYE ---
    l_outer = landmarks[33]
    l_inner = landmarks[133]
    l_iris = landmarks[468]
    l_top = landmarks[159]
    l_bottom = landmarks[145]

    l_width = l_inner.x - l_outer.x
    l_iris_x = (l_iris.x - l_outer.x) / l_width if l_width != 0 else 0.5
    l_height = l_bottom.y - l_top.y
    l_iris_y = (l_iris.y - l_top.y) / l_height if l_height != 0 else 0.5

    # --- RIGHT EYE ---
    r_outer = landmarks[362]
    r_inner = landmarks[263]
    r_iris = landmarks[473]
    r_top = landmarks[386]
    r_bottom = landmarks[374]

    r_width = r_inner.x - r_outer.x
    r_iris_x = (r_iris.x - r_outer.x) / r_width if r_width != 0 else 0.5
    r_height = r_bottom.y - r_top.y
    r_iris_y = (r_iris.y - r_top.y) / r_height if r_height != 0 else 0.5

    # --- fallback if one eye fails ---
    if not (0 <= l_iris_x <= 1 and 0 <= r_iris_x <= 1):
        iris_x_avg = l_iris_x if 0 <= l_iris_x <= 1 else r_iris_x
    else:
        iris_x_avg = (l_iris_x + r_iris_x) / 2

    if not (0 <= l_iris_y <= 1 and 0 <= r_iris_y <= 1):
        iris_y_avg = l_iris_y if 0 <= l_iris_y <= 1 else r_iris_y
    else:
        iris_y_avg = (l_iris_y + r_iris_y) / 2

    # --- GAZE ---
    if iris_x_avg < 0.42:
        gaze = "left"
    elif iris_x_avg > 0.58:
        gaze = "right"
    elif iris_y_avg < 0.4:
        gaze = "up"
    elif iris_y_avg > 0.6:
        gaze = "down"
    else:
        gaze = "center"

    # --- HEAD POSE ---
    nose_tip = landmarks[1]
    chin = landmarks[152]
    left_cheek = landmarks[234]
    right_cheek = landmarks[454]

    pitch = chin.y - nose_tip.y
    roll = right_cheek.y - left_cheek.y

    if abs(roll) > 0.1:
        head_pose = "tilted"
    elif pitch > 0.15:
        head_pose = "down"
    elif pitch < 0.05:
        head_pose = "up"
    else:
        head_pose = "neutral"

    return gaze, head_pose


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def live_face_check(request):
    user = request.user
    face_image_data = request.data.get("face_image")
    assignment_id = request.data.get("assignment_id")
    question_id = request.data.get("question_id")
    question_type = None

    if not face_image_data or not assignment_id:
        return JsonResponse({"error": "Missing data"}, status=400)

    try:
        assignment = TestAssignment.objects.get(id=assignment_id, student=user)
    except TestAssignment.DoesNotExist:
        return JsonResponse({"error": "Invalid assignment"}, status=404)
    

    if question_id:
        try:
            question  = Question.objects.get(id=question_id)
            question_type = question.type
        except Question.DoesNotExist:
            question_type = None

    format, imgstr = face_image_data.split(";base64,")
    img_bytes = base64.b64decode(imgstr)

    # Decode image for both face and phone
    img_np = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


    #phone detect with yolo
    yolo_results = yolo_model.predict(source=img_rgb, verbose=False)
    boxes = yolo_results[0].boxes.data.cpu().numpy()
    phone_detected = False
    for box in boxes:
        class_id = int(box[5].item())
        if class_id == 67:
            phone_detected = True
            break

    if phone_detected:
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_phone_{timestamp}.jpg", img)
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count = 0,
            anomaly_score = 0.7,
            event_type="mobile_detected",
            event_message="Mobile phone detected in camera frame."
        )
        return JsonResponse({"error": "Mobile phone detected"}, status=200)
        
    #head and gaze detection
    gaze_direction, head_pose = detect_gaze_direction(img)
    
    is_looking_down_allowed = question_type in ["code", "open"]
    
    if gaze_direction in ["left", "right"]:
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_gaze_{gaze_direction}_{timestamp}.jpg", img)
        StudentActivityLog.objects.create(
            assignment = assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count = 1,
            anomaly_score = 0.6,
            event_type="gaze_offscreen",
            event_message=f"Student appears to be looking {gaze_direction}."
        )
    elif gaze_direction == "down" and not is_looking_down_allowed:
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_gaze_down_{timestamp}.jpg", img)
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count=1,
            anomaly_score=0.6,
            event_type="gaze_offscreen",
            event_message="Student appears to be looking down."
        )  
    elif gaze_direction == "inconclusive":
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_gaze_inconclusive_{timestamp}.jpg", img)
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count=0,
            anomaly_score=0.2,
            event_type="gaze_unclear",
            event_message="Could not determine eye direction, possibly due to glasses or lighting."
        )
        

    if head_pose in ["down", "up", "tilted"]:
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_head_{head_pose}_{timestamp}.jpg", img)
        anomaly = 0.6 if head_pose != "tilted" else 0.4
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count=1,
            anomaly_score=anomaly,
            event_type="head_pose_suspicious",
            event_message=f"Student has suspicious head pose: {head_pose}."
        )
        


    face_locations = face_recognition.face_locations(img_rgb)
    encodings = face_recognition.face_encodings(img_rgb)

    if len(face_locations) == 0:
        # No face found
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_noface_{timestamp}.jpg", img)
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count=1,
            anomaly_score=0.5,
            event_type= "no_face_found",
            event_message = "Detected no face"
        )
        return JsonResponse({"error": "No face detected"}, status=200)

    if len(face_locations) > 1:
        # Multiple faces = cheating potential
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_multiplefaces_{timestamp}.jpg", img)
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count=1,
            anomaly_score=1.0,
            event_type="multiple_faces",
            event_message="Detected more than one face in frame"
        )
        return JsonResponse({"error": "Multiple faces detected"}, status=200)

    uploaded_encoding = encodings[0]
    stored_encoding = pickle.loads(user.face_encoding)

    match = face_recognition.compare_faces([stored_encoding], uploaded_encoding, tolerance=0.5)[0]
    if not match:
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_missmatch_{timestamp}.jpg", img)
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count=1,
            anomaly_score=0.9,
            event_type="face_mismatch",
            event_message="Detected a different person than the initial authenticated student.",
        )
        return JsonResponse({"error": "Face mismatch"}, status=200)

    # all good
    if gaze_direction == "center" and head_pose == "neutral" and not phone_detected:
        StudentActivityLog.objects.create(
            assignment=assignment,
            attempt_no=assignment.attempt_no,
            focus_lost_count=0,
            anomaly_score=0.0,
            event_type="face_match",
            event_message="Face matches initial authenticated student and gaze is on the screen.",
        )

    return JsonResponse({"success": True})
