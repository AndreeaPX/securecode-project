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
            "first_name":user.first_name,
            "last_name":user.last_name,
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
            return Response({"error": [str(msg) for msg in e.messages]}, status=400)


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

    

    