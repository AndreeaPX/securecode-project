from users.models.tests import TestAssignment, StudentActivityLog
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


os.makedirs("frame_logs", exist_ok=True)
yolo_model = YOLO("yolov8m.pt")

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def live_face_check(request):
    user = request.user
    face_image_data = request.data.get("face_image")
    assignment_id = request.data.get("assignment_id")

    if not face_image_data or not assignment_id:
        return JsonResponse({"error": "Missing data"}, status=400)

    try:
        assignment = TestAssignment.objects.get(id=assignment_id, student=user)
    except TestAssignment.DoesNotExist:
        return JsonResponse({"error": "Invalid assignment"}, status=404)

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
            focus_lost_count = 0,
            anomaly_score = 0.7,
            event_type="mobile_detected",
            event_message="Mobile phone detected in camera frame."
        )
        return JsonResponse({"error": "Mobile phone detected"}, status=200)

    face_locations = face_recognition.face_locations(img_rgb)
    encodings = face_recognition.face_encodings(img_rgb)

    if len(face_locations) == 0:
        # No face found
        timestamp = timezone.now().strftime("%Y-%m-%d_%H-%M-%S")
        cv2.imwrite(f"frame_logs/frame_noface_{timestamp}.jpg", img)
        StudentActivityLog.objects.create(
            assignment=assignment,
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
            focus_lost_count=1,
            anomaly_score=0.9,
            event_type="face_mismatch",
            event_message="Detected a different person than the initial authenticated student.",
        )
        return JsonResponse({"error": "Face mismatch"}, status=200)

    # all good
    StudentActivityLog.objects.create(
        assignment=assignment,
        focus_lost_count=0,
        anomaly_score=0.0,
        event_type="face_match",
        event_message="Face matches initial authenticated student.",
        
    )

    return JsonResponse({"success": True})
