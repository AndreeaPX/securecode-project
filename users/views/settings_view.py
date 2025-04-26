from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.serializers import ProfessorProfileSerializer, StudentProfileSerializer

class ProfessorSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'professor':
            return Response({"detail": "Not authorized."}, status=403)
        
        if not hasattr(user, "professor_profile"):
            return Response({"detail": "Professor profile not found."}, status=404)

        serializer = ProfessorProfileSerializer(user.professor_profile)
        return Response(serializer.data)
    

class StudentSettingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'student':
            return Response({"detail": "Not authorized."}, status=403)
        if not hasattr(user, "student_profile"):
            return Response({"detail": "Student profile not found."}, status=404)
        serializer = StudentProfileSerializer(user.student_profile)
        return Response(serializer.data)