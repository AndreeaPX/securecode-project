"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from users.views.face_login_admin import face_login_admin
from users.views.auth_views import CustomLoginView
from users.views.csrf import get_csrf_token
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="custom_login"),
    path('admin/', admin.site.urls),
    path("api/", include("users.urls")),
    path("face-login-admin/", face_login_admin, name="face_login_admin"),
    path("csrf/", get_csrf_token, name = "get_csrf"),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
