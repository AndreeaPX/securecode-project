from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.questions_view import QuestionViewApi, CoursesAPIView
from .views.tests_view import TestViewSet, TestQuestionViewSet, TestQuestionsByTestIdAPIView, TestAssignmentViewSet, AssignedTestQuestionsAPIView

from .views.auth_views import (
    UserLoginAPIView,
    UserLogoutAPIView,
    ChangePasswordAPIView,
)

from .views.settings_view import (
    ProfessorSettingsAPIView,
    StudentSettingsAPIView,
)

from .views.grade_view import AssignmentReviewAPIView
from .views.visuals_view import AssignmentProgressAPIView, OverallProgressAPIView, GradingProgressAPIView

from .views.attachments_view import QuestionAttachmentAPIView
from rest_framework_simplejwt.views import TokenRefreshView
from .views.test_assignment_view import TestAssignmentDetailView
from .views.face_login_admin import face_login_react
from .views.webcamera_proctoring_view import live_face_check
from .views.student_view import StudentCoursesAPIView, StudentActiveTestsGroupedByCourseAPIView
from .views.submit_view import SubmitAnswersView
from .views.mouse_keyboard_view import mouse_keyboard_check
from .views.audio_analysis import live_audio_check
from .views.professor_marks_view import ProfessorMarksViewSet
from .views.marks import MarksListAPIView, MarksAssignmentsAPIView


router = DefaultRouter()
router.register(r'questions', QuestionViewApi, basename='questions')
router.register(r'tests',TestViewSet, basename='tests')
router.register(r'test-questions', TestQuestionViewSet, basename='test-questions')
router.register(r"test-assignments", TestAssignmentViewSet, basename="test-assignment")
router.register(r"professor/marks", ProfessorMarksViewSet, basename="professor-marks")

urlpatterns = [
    path("login/", UserLoginAPIView.as_view(), name="login-user"),
    path("logout/", UserLogoutAPIView.as_view(), name="logout-user"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("change-password/", ChangePasswordAPIView.as_view(), name="change-password"),
    path("settings/professor/", ProfessorSettingsAPIView.as_view(), name="professor-settings"),
    path("settings/student/", StudentSettingsAPIView.as_view(), name="student-settings"),
    path('courses/', CoursesAPIView.as_view(), name='courses-list'),
    path("questions/<int:question_id>/attachments/", QuestionAttachmentAPIView.as_view(), name="upload-question-attachment"),
    path('tests/<int:test_id>/questions/', TestQuestionsByTestIdAPIView.as_view(), name='test-questions-by-test'),
    path("face-login/", face_login_react, name="face-login-react"),
    path("proctoring/live-face-check/", live_face_check, name = "live_face_check"),
    path("proctoring/mouse_keyboard_check/", mouse_keyboard_check, name = "mouse_keyboard_check"),
    path("proctoring/live-audio-check/", live_audio_check, name="live_audio_check"),
    path("dashboard/student-courses/", StudentCoursesAPIView.as_view(), name="student-dashboard-courses"),
    path("student/tests-by-course/", StudentActiveTestsGroupedByCourseAPIView.as_view(), name="student-tests-by-course"),
    path("test-assignments/<int:assignment_id>/questions/", AssignedTestQuestionsAPIView.as_view(), name="assigned-test-questions"),
    path("test-assignments/<int:pk>/start/", TestAssignmentDetailView.as_view()),
    path("submit-answers/", SubmitAnswersView.as_view(), name="submit-answers"),
    path("marks/", MarksListAPIView.as_view(), name="marks-list"),
    path("marks/<int:test_id>/", MarksAssignmentsAPIView.as_view(), name="marks-detail"),
    path("assignments/<int:pk>/review/",AssignmentReviewAPIView.as_view(), name = "assignment-review"),
    path("assignments/progress/", AssignmentProgressAPIView.as_view(), name="assignment-progress"),
    path("assignments/overall-progress/", OverallProgressAPIView.as_view()),
    path("assignments/grading-progress/", GradingProgressAPIView.as_view(), name="grading-progress"),

    path('', include(router.urls)),
]

