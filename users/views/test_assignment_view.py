from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from users.models.tests import TestAssignment
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_datetime
from django.utils import timezone

class TestAssignmentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        try:
            assignment = TestAssignment.objects.get(id=pk, student=request.user)
        except TestAssignment.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # only set once
        if "started_at" in request.data and assignment.started_at is None:
            raw_dt = request.data["started_at"]
            parsed_dt = parse_datetime(raw_dt)

            if parsed_dt is None:
                return Response({"detail": "Invalid datetime format."}, status=status.HTTP_400_BAD_REQUEST)

            if timezone.is_naive(parsed_dt):
                parsed_dt = timezone.make_aware(parsed_dt)

            assignment.started_at = parsed_dt
            assignment.save(update_fields=["started_at"])

        return Response({"started_at": assignment.started_at})
