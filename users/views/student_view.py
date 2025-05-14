# users/views/dashboard_view.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.serializers.student_serializers import StudentCourseSerializer

class StudentCoursesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != 'student' or not hasattr(user, 'student_profile'):
            return Response({"detail": "Not authorized or student profile missing."}, status=403)

        courses = user.student_profile.courses.all()
        serializer = StudentCourseSerializer(courses, many=True)
        return Response(serializer.data)
