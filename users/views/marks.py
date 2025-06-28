from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from users.models.tests import Test, TestAssignment
from users.serializers.marks import (
    TestSummarySerializer,
    AssignmentListSerializer,
)
from django.utils.dateparse import parse_date

class MarksListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "professor":
            return Response({"detail": "Forbidden"}, status=403)

        qs = Test.objects.filter(professor=user)
        ttype   = request.GET.get("type")
        if ttype:
            qs = qs.filter(type=ttype)

        start_date = request.GET.get("start_time__date")
        if start_date:
            qs = qs.filter(start_time__date=parse_date(start_date))

        status = request.GET.get("status")
        if status == "finalized":
            qs = qs.annotate(
                unfinished=Count("assignments", filter=Q(assignments__finished_at__isnull=True))
            ).filter(unfinished=0)
        elif status == "in progress":
            qs = qs.filter(assignments__finished_at__isnull=True).distinct()

        search = request.GET.get("search")
        if search:
            qs = qs.filter(name__icontains=search)
        qs = qs.annotate(
                total_assignments=Count("assignments"),
                finalized_count=Count("assignments", filter=Q(assignments__finished_at__isnull=False)),
            ).order_by("-created_at")

        data = TestSummarySerializer(qs, many=True).data
        return Response(data)


class MarksAssignmentsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, test_id):
        user = request.user
        if user.role != "professor":
            return Response({"detail": "Forbidden"}, status=403)

        try:
            test = Test.objects.get(id=test_id, professor=user)
        except Test.DoesNotExist:
            return Response({"detail": "Not found."}, status=404)

        assignments = (
            TestAssignment.objects
            .filter(test=test)
            .select_related("student")   
            .order_by("student__last_name", "student__first_name", "attempt_no")
        )

        data = AssignmentListSerializer(assignments, many=True).data
        return Response(data)
