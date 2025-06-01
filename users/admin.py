from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.crypto import get_random_string
from datetime import timedelta
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.urls import path
from django.conf import settings

from .models.core import User, UserInvitation, Faculty, Specialization, Course, StudentProfile, ProfessorProfile, Series, Group
from .forms import CustomUserChangeForm, CustomUserCreationForm

from .models.questions import Question, AnswerOption, QuestionAttachment
from .models.tests import Test,TestQuestion,TestAssignment,StudentAnswer,StudentActivityLog, StudentActivityAnalysis



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

            UserInvitation.objects.filter(email=obj.email).delete()

            UserInvitation.objects.create(
                email = obj.email,
                role = obj.role,
                otp_token=otp_hash,
                is_used = False,
                expires_at = expires_at,
                failed_attempts = 0,
                invited_by  = request.user
            )

            login_url = "https://localhost:5173/login"
            if obj.role == "admin":
                login_url = "https://localhost:8000/admin/"
            try:
                # send_mail(
                #     subject="You're invited to SecureCode",
                #     message=(
                #         f"Hello,\n\n"
                #         f"You’ve been added to SecureCode as a {obj.role}.\n"
                #         f"Use this one-time code: {otp_token}\n"
                #         f"Login here: {login_url}\n\n"
                #         f"This code expires in 24 hours.\n\n"
                #         f"– SecureCode Team"
                # ),
                # from_email=settings.DEFAULT_FROM_EMAIL,
                # recipient_list=[obj.email],
                # fail_silently=False,
                # )
                print(otp_token)
                print(obj.email)
            except Exception as e :
                self.message_user(request, f"User created but email failed: {str(e)}", level='error')
        else:
            super().save_model(request=request, obj=obj, form=form, change=change)


@admin.register(Faculty)
class CustomFacultyAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj = None):
        return request.user.is_superuser
    
@admin.register(Specialization)
class CustomSpecializationAdmin(admin.ModelAdmin):
    search_fields = ("name", "code")
    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj = None):
        return request.user.is_superuser
    
@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "group_type", "specialization")
    list_filter = ("year", "group_type", "specialization__name")
    search_fields = ("name",)
    autocomplete_fields = ("specialization",)

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("number", "series")
    list_filter = ("series__year", "series__group_type")
    search_fields = ("number",)
    autocomplete_fields = ("series",)

@admin.register(Course)
class CustomCourseAdmin(admin.ModelAdmin):
    search_fields = ("name", "code")
    list_display = ("name", "code", "year", "semester", "is_optional", "specialization")
    list_filter = ("year", "semester", "is_optional", "specialization__faculty")

    def has_add_permission(self, request):
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj = None):
        return request.user.is_superuser

@admin.register(StudentProfile)
class CustomStudentProfileAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)
    autocomplete_fields = ('user', 'specialization', 'courses')
    list_display = ("user","group_type","group", "year", "specialization")
    list_filter = ("user","group_type", "group","year", "specialization", "specialization__faculty")
    
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

        courses = Course.objects.filter(year=year,specialization_id=specialization).values("id", "name")
        return JsonResponse(list(courses), safe=False)   
        
@admin.register(ProfessorProfile)
class ProfessorProfileAdmin(admin.ModelAdmin):
    search_fields = ("user__email",)
    autocomplete_fields = ('user', 'specialization', 'courses', 'seminar_groups', 'lecture_series')
    list_display = ("user__email", "specialization", "teaches_lecture", "teaches_seminar")
    list_filter = ("teaches_lecture", "teaches_seminar", "specialization", "specialization__faculty")
    filter_horizontal = ("seminar_groups", "lecture_series")

   
class QuestionAttachmentInline(admin.TabularInline):
    model = QuestionAttachment
    extra = 1

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [QuestionAttachmentInline]
    list_display = ("text", "type", "course", "created_by", "is_shared", "is_generated_ai", "is_code_question", "language")
    list_filter = ("type", "is_shared", "is_generated_ai", "course")
    search_fields = ("text",)
    readonly_fields = [f.name for f in Question._meta.fields]


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ("question", "text", "is_correct")
    search_fields = ("text",)
    list_filter = ("is_correct",)
    readonly_fields = [f.name for f in AnswerOption._meta.fields]


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "course", "professor", "start_time", "deadline")
    list_filter = ("type", "course", "professor")
    search_fields = ("name",)
    readonly_fields = [f.name for f in Test._meta.fields]


@admin.register(TestQuestion)
class TestQuestionAdmin(admin.ModelAdmin):
    list_display = ("test", "question", "order", "is_required")
    search_fields = ("question__text",)
    list_filter = ("is_required",)
    readonly_fields = [f.name for f in TestQuestion._meta.fields]


@admin.register(TestAssignment)
class TestAssignmentAdmin(admin.ModelAdmin):
    list_display = ("test", "student", "started_at", "finished_at", "attempt_no")
    search_fields = ("student__email",)
    list_filter = ("test", "student")
    readonly_fields = [
        f.name for f in TestAssignment._meta.fields if f.name not in ["manual_score", "reviewed_by"]
    ]


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ("assignment", "question", "needs_manual_review")
    search_fields = ("assignment__student__email", "question__text")
    list_filter = ("needs_manual_review",)
    readonly_fields = [f.name for f in StudentAnswer._meta.fields]


@admin.register(StudentActivityLog)
class StudentActivityLogAdmin(admin.ModelAdmin):
    list_display = ("assignment_id_display", "event_type", "timestamp", "anomaly_score")
    list_filter = ("event_type", "assignment__id")
    search_fields = ("assignment__id", "event_type", "event_message")
    readonly_fields = [f.name for f in StudentActivityLog._meta.fields]

    def assignment_id_display(self, obj):
        return f"Assignment #{obj.assignment.id}"
    assignment_id_display.short_description = "Assignment"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
@admin.register(StudentActivityAnalysis)
class StudentActivityAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "assignment_id_display",
        "esc_pressed",
        "second_screen_events",
        "tab_switches",
        "window_blurs",
        "total_key_presses",
        "average_key_delay",
        "copy_paste_events",
        "is_suspicious",
        "analyzed_at"
    )
    list_filter = ("is_suspicious", "assignment__id")
    search_fields = ("assignment__id",)
    readonly_fields = [f.name for f in StudentActivityAnalysis._meta.fields]

    def assignment_id_display(self, obj):
        return f"Assignment #{obj.assignment.id}"
    assignment_id_display.short_description = "Assignment"

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False