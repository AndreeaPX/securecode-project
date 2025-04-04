from rest_framework.generics import GenericAPIView
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.password_validation import validate_password
from users.serializers import UserLoginSerializer
from users.forms import CustomLoginForm
from django.contrib.auth import login
from django.views.generic import FormView
from django.urls import reverse_lazy

class UserLoginAPIView(GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data

        if user.role == "admin" and user.first_login:
            user.first_login = False
            user.save()

        refresh = RefreshToken.for_user(user)
        return Response({
            "id": user.id,
            "email": user.email,
            "role": user.role,
            "first_login": user.first_login,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        })


class UserLogoutAPIView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)




class ChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not new_password or not confirm_password:
            return Response({"error": "All fields are required."}, status=400)

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match."}, status=400)

        try:
            validate_password(new_password)
        except Exception as e:
            return Response({"error": list(e)}, status=400)

        user.set_password(new_password)
        user.first_login = False
        user.save()

        return Response({"detail": "Password successfully changed."}, status=200)

class CustomLoginView(FormView):
    template_name = "admin/login.html"
    form_class = CustomLoginForm
    success_url = reverse_lazy("admin:index")

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return super().form_valid(form)
    

# import base64
# import face_recognition
# import numpy as np
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django.contrib.auth import login
# from users.models import User

# @csrf_exempt
# def face_login_admin_api(request):
#     if request.method != "POST":
#         return JsonResponse({"success": False, "message": "Invalid request method"})

#     email = request.POST.get("email")
#     image_data = request.POST.get("image")

#     if not email or not image_data:
#         return JsonResponse({"success": False, "message": "Missing email or image"})

#     try:
#         user = User.objects.get(email=email)
#     except User.DoesNotExist:
#         return JsonResponse({"success": False, "message": "User does not exist"})

#     try:
#         # decode base64 -> image array
#         header, encoded = image_data.split(",", 1)
#         image_bytes = base64.b64decode(encoded)
#         image_np = face_recognition.load_image_file(io.BytesIO(image_bytes))

#         face_locations = face_recognition.face_locations(image_np)
#         if len(face_locations) != 1:
#             return JsonResponse({"success": False, "message": "Face not found or multiple faces detected."})

#         face_encoding = face_recognition.face_encodings(image_np, known_face_locations=face_locations)[0]

#         if user.face_encoding is None:
#             user.face_encoding = face_encoding.tobytes()
#             user.save()
#             login(request, user)
#             return JsonResponse({"success": True, "message": "Face registered"})
#         else:
#             known_encoding = np.frombuffer(user.face_encoding, dtype=np.float64)
#             match = face_recognition.compare_faces([known_encoding], face_encoding)[0]
#             if match:
#                 login(request, user)
#                 return JsonResponse({"success": True, "message": "Face recognized, logged in"})
#             else:
#                 return JsonResponse({"success": False, "message": "Face does not match"})
#     except Exception as e:
#         return JsonResponse({"success": False, "message": f"Error processing image: {str(e)}"})
