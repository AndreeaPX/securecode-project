from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.serializers.student_serializers import SubmitAnswersSerializer
from users.models.tests import TestAssignment
from users.views.mouse_keyboard_view import analyze_assignment_logs  

class SubmitAnswersView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SubmitAnswersSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        assignment_id = serializer.validated_data["assignment_id"]
        try:
            assignment = TestAssignment.objects.select_related("test").get(id=assignment_id, student=request.user)
            if assignment.test.has_ai_assistent:
                analyze_assignment_logs(assignment)
        except TestAssignment.DoesNotExist:
            pass 
        return Response(result)
