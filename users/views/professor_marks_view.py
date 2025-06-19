from rest_framework import viewsets, permissions
from users.models.tests import TestAssignment
from users.serializers.assignment import ProfessorAssignmentSerializer

class ProfessorMarksViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Returns every TestAssignment that belongs to tests
    authored by the current professor.
    """
    serializer_class = ProfessorAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return (
            TestAssignment.objects
            .filter(test__professor=self.request.user)          
            .select_related("student", "test")                 
            .prefetch_related("answers__selected_options")
            .order_by("-id")
        )
