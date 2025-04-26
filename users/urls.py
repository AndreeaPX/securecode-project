from django.urls import path
from .views.auth_views import (
    UserLoginAPIView,
    UserLogoutAPIView,
    ChangePasswordAPIView,
)

from .views.settings_view import (
    ProfessorSettingsAPIView,
    StudentSettingsAPIView,
)

from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("login/", UserLoginAPIView.as_view(), name="login-user"),
    path("logout/", UserLogoutAPIView.as_view(), name="logout-user"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("settings/professor/", ProfessorSettingsAPIView.as_view(), name="professor-settings"),
    path("settings/student/", StudentSettingsAPIView.as_view(), name="student-settings"),
]
