from rest_framework import viewsets, permissions, serializers
from users.models.tests import Test, TestQuestion
from users.serializers.tests import TestSerializer, TestQuestionSerializer, TestQuestionDetailedSerializer
from rest_framework.exceptions import PermissionDenied, NotFound
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action


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
        serializer.save(professor = user)

    def get_object(self):
        obj = super().get_object()
        if obj.professor != self.request.user:
            raise PermissionDenied("You don't have permission to modify this test.")
        return obj

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