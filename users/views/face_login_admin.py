import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.contrib.auth import login
from users.models.core import User
import face_recognition
import tempfile
import os
import pickle
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from users.throttles import SafeLoginThrottle
from rest_framework.permissions import IsAuthenticated
from .face_validators import validate_face_image
import cv2

@api_view(['GET','POST'])
@throttle_classes([SafeLoginThrottle])
@csrf_protect
def face_login_admin(request):

    if request.method == 'GET':
        return render(request, 'face_login_admin.html')

    if request.method == "POST":
        try:
            email = request.POST.get("email")
            face_image_data = request.POST.get("face_image")

            if not email or not face_image_data:
                return JsonResponse({"error": "Missing essential data."}, status=400)

            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({"error": "User not found."}, status=404)
            
            if not (user.role == "admin" or user.is_staff or user.is_superuser):
                return JsonResponse({"error": "Access denied: Not an admin/staff user."}, status=403)

            if user.failed_face_attempts >= 5:
                return JsonResponse({"error": "Too many failed attempts."}, status=429)

            format, imgstr = face_image_data.split(";base64,")
            ext = format.split("/")[-1]
            file_name = f"{user.email.replace('@', '_at_')}_face.{ext}"
            img_bytes = base64.b64decode(imgstr)


            is_valid, result = validate_face_image(img_bytes=img_bytes)
            if not is_valid:
                return JsonResponse({"error": result}, status=400)
            
            img_cv2 = result
            img_rgb = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)

            uploaded_encodings = face_recognition.face_encodings(img_rgb)

            if len(uploaded_encodings) != 1:
                return JsonResponse({"error": "Image must contain exactly one face."}, status=400)
            
            uploaded_encoding = uploaded_encodings[0]

            if user.face_encoding is None:
                user.face_image.save(file_name, ContentFile(img_bytes))
                user.face_encoding = pickle.dumps(uploaded_encoding)
                user.failed_face_attempts = 0
                user.save()
                user.backend = 'users.backends.FaceAuthBackend'
                login(request, user)
                SafeLoginThrottle.reset(request)
                return JsonResponse({"success": True, "message": "Face registered & logged in."})

            stored_encoding = pickle.loads(user.face_encoding)
            match = face_recognition.compare_faces([stored_encoding], uploaded_encoding, tolerance=0.5)[0]
            if match:
                user.failed_face_attempts = 0
                user.save()
                user.backend = 'users.backends.FaceAuthBackend'
                login(request, user)
                SafeLoginThrottle.reset(request)
                return JsonResponse({"success": True, "message": "Login successful."})
            else: 
                user.failed_face_attempts+=1
                user.save()
                return JsonResponse({"error": "Face does not match."}, status=401)
        except Exception as e:
             return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
    


@api_view(['POST'])
@throttle_classes([SafeLoginThrottle])
@permission_classes([IsAuthenticated])
def face_login_react(request):
    try:
        user = request.user
        face_image_data = request.data.get("face_image")

        if not face_image_data:
            return JsonResponse({"error": "Missing face image."}, status=400)

        if user.failed_face_attempts >= 5:
            return JsonResponse({"error": "Too many failed attempts."}, status=429)

        format, imgstr = face_image_data.split(";base64,")
        img_bytes = base64.b64decode(imgstr)

        is_valid, result = validate_face_image(img_bytes)
        if not is_valid:
            return JsonResponse({"error": result}, status=400)

        
        img_cv2 = result
        img_rgb = cv2.cvtColor(img_cv2, cv2.COLOR_BGR2RGB)
        uploaded_encodings = face_recognition.face_encodings(img_rgb)

        if len(uploaded_encodings) != 1:
            return JsonResponse({"error": "Exactly one face must be present."}, status=400)

        uploaded_encoding = uploaded_encodings[0]

        if user.face_encoding is None:
            user.face_encoding = pickle.dumps(uploaded_encoding)
            user.failed_face_attempts = 0
            user.save()
            SafeLoginThrottle.reset(request)
            return JsonResponse({"success": True, "first_time": True})

        stored_encoding = pickle.loads(user.face_encoding)
        match = face_recognition.compare_faces([stored_encoding], uploaded_encoding, tolerance=0.50)[0]

        if match:
            user.failed_face_attempts = 0
            user.save()
            SafeLoginThrottle.reset(request)
            return JsonResponse({"success": True, "first_time": user.first_login})
        else:
            user.failed_face_attempts += 1
            user.save()
            return JsonResponse({"error": "Face mismatch."}, status=401)

    except Exception as e:
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)

