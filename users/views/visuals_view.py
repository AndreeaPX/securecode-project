from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from users.models.tests import Test, TestAssignment

from users.serializers.visuals import AssignmentProgressSerializer, GradingProgressRowSerializer

class AssignmentProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tests = (
            Test.objects.filter(professor=request.user)
            .annotate(
                total_assigned=Count("assignments"),
                finished=Count("assignments", filter=Q(assignments__finished_at__isnull=False))
            )
            .values("id", "name", "total_assigned", "finished")
        )

        for test in tests:
            total = test["total_assigned"] or 1
            test["progress_percent"] = round((test["finished"] / total) * 100)

        serializer = AssignmentProgressSerializer(tests, many=True)
        return Response(serializer.data)

class OverallProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = TestAssignment.objects.filter(test__professor=request.user)
        total = qs.count()
        finished = qs.filter(finished_at__isnull=False).count()

        return Response({
            "total": total,
            "finished": finished
        })

class GradingProgressAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        professor = request.user
        data = []

        tests = Test.objects.filter(professor=professor).prefetch_related("test_questions", "assignments", "assignments__reviewed_by")

        for test in tests:
            test_name = test.name
            test_id = test.id

            first_q = test.test_questions.first()
            question_type = first_q.question.get_type_display() if first_q else "Mixed"

            assignments = test.assignments.all()

            if any(a.auto_score is None and a.manual_score is None for a in assignments):
                status = "Awaiting correction."
            elif all(a.auto_score is not None for a in assignments):
                status = "Auto Corrected."
            else:
                reviewer = next((a.reviewed_by for a in assignments if a.reviewed_by), None)
                if reviewer:
                    status = f"{reviewer.first_name} {reviewer.last_name}".strip()
                else:
                    status = "Professor"

            data.append({
                "test_id": test_id,
                "test_name": test_name,
                "question_type": question_type,
                "status": status,
            })

        serializer = GradingProgressRowSerializer(data, many=True)
        return Response(serializer.data)
