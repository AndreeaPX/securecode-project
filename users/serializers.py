from rest_framework import serializers
from .models import User, UserInvitation
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
from django.utils import timezone

User = get_user_model()

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role")

User = get_user_model()

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")
        UserInvitation.objects.filter(is_used=False, expires_at__lt=timezone.now()).delete()

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")

        if user.has_usable_password():
            if not user.check_password(password):
                raise serializers.ValidationError("Invalid credentials.")
            return user

        try:
            invitation = UserInvitation.objects.get(email=email, is_used=False)
        except UserInvitation.DoesNotExist:
            raise serializers.ValidationError("OTP invalid or expired.")

        if invitation.is_expired():
            raise serializers.ValidationError("OTP has expired.")

        if invitation.failed_attempts >= 5:
            raise serializers.ValidationError("Too many failed attempts.")

        if not check_password(password, invitation.otp_token):
            invitation.failed_attempts += 1
            invitation.save()
            raise serializers.ValidationError("Invalid OTP code.")

        user.first_login = True
        user.save()

        invitation.is_used = True
        invitation.failed_attempts = 0
        invitation.otp_token = None
        invitation.save()

        return user
