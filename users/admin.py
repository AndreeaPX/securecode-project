from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.urls import path

from .models import User, UserInvitation, Faculty, Specialization, Course, StudentProfile, ProfessorProfile
from .forms import CustomUserChangeForm, CustomUserCreationForm


@admin.register(User)
class CustomAdminUser(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User

    list_display = ("email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")

    fieldsets = (
    (None, {"fields": ("email", "first_name", "last_name", "start_date")}),
    ("Permissions", {"fields": ("is_staff", "is_active", "role", "groups", "user_permissions")}),
    ("Login Status", {"fields": ("first_login",)}),
    ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
    (None, {
        "classes": ("wide",),
        "fields": ("email", "first_name", "last_name", "start_date", "role", "is_staff", "is_active", "first_login"),
    }),
    )

    search_fields = ("email",)
    ordering = ("email",)

    def save_model(self, request, obj, form, change):
        is_new = not change

        if is_new:

            otp_token = get_random_string(length=32)
            otp_hash = make_password(otp_token)
            expires_at = timezone.now() + timedelta(hours=24)

            obj.set_unusable_password()
            super().save_model(request=request,obj=obj, form=form,change=change)

            UserInvitation.objects.filter(email=obj.email, is_used=False)

            UserInvitation.objects.update_or_create(
                email = obj.email,
                defaults={
                    "role": obj.role,
                    "otp_token": otp_hash,
                    "is_used": False,
                    "expires_at": expires_at,
                },
            )

            print(otp_hash)
            print(otp_token)

            if obj.role == "admin":
                login_url = "http://localhost:8000/admin/"
            else:
                login_url = "http://localhost:5173/login"

            send_mail(
                subject="You're invited to SecureCode",
                message=(
                    f"Hello,\n\n"
                    f"You’ve been added to SecureCode as a {obj.role}.\n"
                    f"Use this one-time code: {otp_token}\n"
                    f"Login here: {login_url}\n\n"
                    f"This code expires in 24 hours.\n\n"
                    f"– SecureCode Team"
            ),
                from_email="panandreea77@gmail.com",
                recipient_list=[obj.email],
                fail_silently=False,
            )
        else :
            super().save_model(request=request,obj=obj,form=form, change=change)

@admin.register(Faculty)
class CustomFacultyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj = None):
        return request.user.is_superuser
    
@admin.register(Specialization)
class CustomSpecializationAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj = None):
        return request.user.is_superuser

@admin.register(Course)
class CustomCourseAdmin(admin.ModelAdmin):

    list_display = ("name", "code", "year", "semester", "is_optional", "specialization")
    list_filter = ("year", "semester", "is_optional", "specialization__faculty")

    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj = None):
        return request.user.is_superuser

@admin.register(StudentProfile)
class CustomStudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user","group_type","group", "year", "specialization")
    list_filter = ("user","group_type", "group","year", "specialization", "specialization__faculty")
    search_fields = ("user__email",)
    class Media:
        js = ('js/dynamic_course_filter.js',)


    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("fetch-courses/", self.admin_site.admin_view(self.fetch_courses), name="fetch_courses"),
        ]
        return custom_urls + urls

    def fetch_courses(self, request):
        year = request.GET.get("year")
        specialization = request.GET.get("specialization")

        if not (year and specialization):
            return JsonResponse([], safe=False)

        filter_key = f"{year}_{specialization}"
        courses = Course.objects.filter(filter_key=filter_key).values("id", "name")

        return JsonResponse(list(courses), safe=False)   
        
@admin.register(ProfessorProfile)
class ProfessorProfileAdmin(admin.ModelAdmin):
    list_display = ("specialization", "teaches_lecture", "teaches_seminar")
    list_filter = ("teaches_lecture", "teaches_seminar", "specialization", "specialization__faculty")
    search_fields = ("user__email",)
