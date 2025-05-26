from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from users.serializers.student_serializers import SubmitAnswersSerializer

class SubmitAnswersView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = SubmitAnswersSerializer(data = request.data, context = {"request":request})
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        return Response(result)
    
    