from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import Throttled

class BurstRateThrottle(UserRateThrottle):
    scope = 'burst'

class SustainedRateThrottle(UserRateThrottle):
    scope = 'sustained'

class FaceLoginThrottle(UserRateThrottle):
    scope = 'face_login'
    def throttle_failure(self):
        raise Throttled(detail="Too many failed face login attempts. Try again later.")