from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import Throttled
from django.core.cache import cache
from django.core.mail import send_mail

class SafeLoginThrottle(UserRateThrottle):
    scope = 'safe_login'

    def allow_request(self, request, view):
        if request.method in ['GET', 'OPTIONS']:
            return True

        # Dacă POST la login / refresh / face-login -> throttling
        if not super().allow_request(request, view):
            self.throttle_failure()
        return True

    def throttle_failure(self):
        send_mail(
        'Login attempts exceeded!',
        'Someone exceeded login attempts!',
        'panandreea77@gmail.com',
        ['panandreea77@gmail.com'],
        fail_silently=True,
        )
        raise Throttled(detail="Too many login attempts. Please wait a few minutes and retry.")

    @staticmethod
    def reset(request):
        """
        Clear throttling cache for a user/ip after successful login/refresh.
        """
        key = SafeLoginThrottle().get_cache_key(request, None)
        if key:
            cache.delete(key)

