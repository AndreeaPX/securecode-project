import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.contrib.auth import login
from users.models import User
import face_recognition
import tempfile
import os
import pickle
from rest_framework.decorators import api_view, throttle_classes
from users.throttles import FaceLoginThrottle


@api_view(['GET','POST'])
@throttle_classes([FaceLoginThrottle])
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

            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name

            uploaded_image = face_recognition.load_image_file(tmp_path)
            uploaded_encodings = face_recognition.face_encodings(uploaded_image)

            os.remove(tmp_path)

            if len(uploaded_encodings) != 1:
                return JsonResponse({"error": "Image must contain exactly one face."}, status=400)
            
            uploaded_encoding = uploaded_encodings[0]

            if user.face_encoding is None:
                user.face_image.save(file_name, ContentFile(img_bytes))
                user.face_encoding = pickle.dumps(uploaded_encoding)
                user.failed_face_attempts = 0
                user.save()
                login(request, user)
                return JsonResponse({"success": True, "message": "Face registered & logged in."})

            stored_encoding = pickle.loads(user.face_encoding)
            match = face_recognition.compare_faces([stored_encoding], uploaded_encoding, tolerance=0.40)[0]

            if match:
                user.failed_face_attempts = 0
                user.save()
                login(request, user)
                return JsonResponse({"success": True, "message": "Login successful."})
            else: 
                user.failed_face_attempts+=1
                user.save()
                return JsonResponse({"error": "Face does not match."}, status=401)
        except Exception as e:
             return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
    
