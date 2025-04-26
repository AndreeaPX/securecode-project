from django.contrib.auth.backends import BaseBackend
from users.models.core import User


class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=email)
            if user.has_usable_password() and user.check_password(password):
                return user
        except User.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

class FaceAuthBackend(BaseBackend):
    def authenticate(self, request, user=None, **kwargs):
        if user and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        from users.models.core import User
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
