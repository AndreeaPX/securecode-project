from rest_framework import generics, permissions, status
from rest_framework.response import Response
from users.models.tests import TestAssignment
from users.serializers.grade import AssignmentReviewSerializer  

class AssignmentReviewAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = AssignmentReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            TestAssignment.objects
            .filter(test__professor=self.request.user)
            .select_related("student", "test")
            .prefetch_related(
                "answers",
                "answers__question",
                "answers__question__attachments",
                "answers__question__options",
            )
        )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.test.show_result:
            for ans in request.data.get("answers", []):
                if "points" in ans:
                    return Response(
                        {"detail": "Points cannot be modified on an auto-graded assignment."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
        return super().update(request, *args, **kwargs)


