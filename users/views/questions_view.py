from rest_framework import generics, permissions, viewsets, filters
from users.models.questions import Question
from users.models.core import Course
from users.serializers.questions import QuestionSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import PermissionDenied
from users.serializers.core import CourseSerializer

class CoursesAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CourseSerializer

    def get_queryset(self):
        user = self.request.user
        if user.role == 'professor':
            try:
                return user.professor_profile.courses.all()
            except:
                return Course.objects.none()
        return Course.objects.none()

class IsOwnerOrReadOnlyPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.created_by == request.user

class QuestionViewApi(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnlyPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['course', 'type', 'created_at', 'is_code_question', 'created_by__email']
    ordering_fields = ['created_at', 'points']
    search_fields = ['text', 'created_by__email', 'created_by__first_name', 'created_by__last_name']

    def get_queryset(self):
        user = self.request.user

        if user.role == "professor":
            if hasattr(user, 'professor_profile'):
                courses_ids = user.professor_profile.courses.values_list('id', flat=True)
                return Question.objects.filter(course_id__in=courses_ids).prefetch_related('options')
            else:
                return Question.objects.none()
        else:  # to be modified
            return Question.objects.none()
