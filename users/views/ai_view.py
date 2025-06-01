from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.models.tests import TestAssignment
from users.ai_engine.preprocessing import get_lstm_sequence

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def test_lstm_sequence(request, assignment_id):
    user = request.user
    try:
        assignment = TestAssignment.objects.get(id=assignment_id, student=user)
    except TestAssignment.DoesNotExist:
        return Response({"error": "Assignment not found"}, status=404)

    sequence = get_lstm_sequence(assignment)
    return Response({"sequence": sequence})
