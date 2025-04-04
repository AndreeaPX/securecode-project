from rest_framework import serializers
from .models import User, UserInvitation
from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.hashers import check_password
from django.utils import timezone

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

        UserInvitation.objects.filter(is_used=False, expires_at__lt=timezone.now()).delete()
        user = authenticate(email=email, password=password)
        if user and user.is_active:
            return user

        try:
            invitation = UserInvitation.objects.get(email=email, is_used=False)
        except UserInvitation.DoesNotExist:
            raise serializers.ValidationError("We are so sorry, but you can not login because you don't have an invite. Please try to reach out to an admin.")

        if invitation.is_expired():
            raise serializers.ValidationError("This link is not available anymore.")

        if invitation.failed_attempts >= 5:
            raise serializers.ValidationError("Too many failed attempts. Please contact support or request a new code.")

        if password and check_password(password, invitation.otp_token):
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("This credentials do not match.")

            user.first_login = True
            user.save()

            invitation.is_used = True
            invitation.failed_attempts = 0
            invitation.otp_token = None
            invitation.save()
            

            return user
        invitation.failed_attempts += 1
        invitation.save()
        raise serializers.ValidationError("Invalid email or password.")