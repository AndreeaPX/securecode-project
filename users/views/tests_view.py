from rest_framework import viewsets, permissions, serializers
from users.models.tests import Test, TestQuestion, TestAssignment
from users.serializers.tests import TestSerializer, TestQuestionSerializer, TestQuestionDetailedSerializer, TestAssignmentSerializer
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from users.serializers.questions import StudentQuestionSerializer
import random

class TestViewSet(viewsets.ModelViewSet):
    serializer_class = TestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role!="professor":
            raise PermissionDenied("Only professors can view their own tests.")
        return Test.objects.filter(professor=user)
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.role != "professor":
            raise PermissionDenied("Only professors can create tests.")
        
        profile = getattr(user, "professor_profile", None)
        if not profile:
            raise PermissionDenied("No professor profile.")
        
        course = serializer.validated_data.get("course")
        if course not in profile.courses.all():
            raise PermissionDenied("You are not assigned to this course.")
        
        target_series = serializer.validated_data.get("target_series")
        target_group = serializer.validated_data.get("target_group")

        
        if target_series and profile.teaches_lecture:
            if target_series not in profile.lecture_series.all():
                raise PermissionDenied("You're not assigned to this series.")

        if target_group and profile.teaches_seminar:
            if target_group not in profile.seminar_groups.all():
                raise PermissionDenied("You're not assigned to this group.")

        serializer.save(professor = user)


    def perform_update(self, serializer):
        user = self.request.user
        if user.role != "professor":
            raise PermissionDenied("Only professors can update tests.")
        
        profile = getattr(user, "professor_profile", None)
        if not profile:
            raise PermissionDenied("No professor profile.")
        
        course = serializer.validated_data.get("course", serializer.instance.course)
        if course not in profile.courses.all():
            raise PermissionDenied("You are not assigned to this course.")

        target_series = serializer.validated_data.get("target_series", serializer.instance.target_series)
        target_group = serializer.validated_data.get("target_group", serializer.instance.target_group)

        if target_series and profile.teaches_lecture:
            if target_series not in profile.lecture_series.all():
                raise PermissionDenied("You're not assigned to this series.")

        if target_group and profile.teaches_seminar:
            if target_group not in profile.seminar_groups.all():
                raise PermissionDenied("You're not assigned to this group.")

        serializer.save()

    def get_object(self):
        obj = super().get_object()
        if obj.professor != self.request.user:
            raise PermissionDenied("You don't have permission to modify this test.")
        return obj
    
    @action(detail=True, methods=["post"])
    def submit(self, request, pk = None):
        test = self.get_object()
        if test.is_submitted:
            return Response({"detail": "Test already submitted."}, status=400)
        created = test.assign()
        test.is_submitted = True
        test.save()

        return Response({"detail": f"Assigned to {created} students."})

class TestQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = TestQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role != "professor":
            return TestQuestion.objects.none()
        return TestQuestion.objects.filter(test__professor=user)
    
    def perform_create(self, serializer):
        test = serializer.validated_data['test']
        question = serializer.validated_data['question']
        if question.course != test.course:
            raise serializers.ValidationError("Question does not belong to the same course as the test.")
        serializer.save()

    def perform_update(self, serializer):
        test = serializer.validated_data.get('test', serializer.instance.test)
        question = serializer.validated_data.get('question', serializer.instance.question)

        if question != serializer.instance.question:
            raise serializers.ValidationError("You can't change the question. Remove and add another instead.")

        if question.course != test.course:
            raise serializers.ValidationError("Question does not belong to the same course as the test.")
    
        serializer.save()

    @action(detail=False, methods=["delete"], url_path="by-composite")
    def delete_by_composite(self, request):
        test_id = request.data.get("test")
        question_id = request.data.get("question")

        if not test_id or not question_id:
            return Response({"detail": "Missing test or question ID."}, status=400)

        try:
            tq = TestQuestion.objects.get(test_id=test_id, question_id=question_id)
        except TestQuestion.DoesNotExist:
            return Response({"detail": "TestQuestion not found."}, status=404)

        if tq.test.professor != request.user:
            raise PermissionDenied("You cannot delete from this test.")

        tq.delete()
        return Response(status=204)

class TestQuestionsByTestIdAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, test_id):
        try:
            test = Test.objects.get(pk=test_id)
        except Test.DoesNotExist:
            raise NotFound("Test not found.")

        if test.professor != request.user:
            raise PermissionDenied("You do not have access to this test.")

        test_questions = TestQuestion.objects.filter(test=test).select_related('question').prefetch_related('question__options')
        serializer = TestQuestionDetailedSerializer(test_questions, many=True)
        return Response(serializer.data)
    
from rest_framework import viewsets, status
from rest_framework.response import Response

class TestAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = TestAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "professor":
            return TestAssignment.objects.filter(test__professor=user)
        elif user.role == "student":
            return TestAssignment.objects.filter(student=user)
        return TestAssignment.objects.none()

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        # permis doar studentului legat de assignment
        if request.user != instance.student:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_403_FORBIDDEN)

        allowed_fields = {"started_at", "finished_at", "is_submitted"}
        filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}

        serializer = self.get_serializer(instance, data=filtered_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
class AssignedTestQuestionsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assignment_id):
        user = request.user

        try:
            assignment = TestAssignment.objects.select_related("test").get(pk=assignment_id)
        except TestAssignment.DoesNotExist:
            raise NotFound("Test assignment not found.")

        if assignment.student != user:
            raise PermissionDenied("You don't have access to this test.")

        # randomize questions (same every time if needed, otherwise re-shuffle here)
        test_questions = (
            TestQuestion.objects
            .filter(test=assignment.test)
            .select_related("question")
            .prefetch_related("question__options")
        )

        # Optional: shuffle questions here once, store order in session/db
        questions_list = list(test_questions)
        random.shuffle(questions_list)  # for now we random every time (for testing)
        questions = [tq.question for tq in questions_list]
        serializer = StudentQuestionSerializer(questions, many=True)
        return Response(serializer.data)