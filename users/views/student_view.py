from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.serializers.student_serializers import StudentCourseSerializer
from users.serializers.tests import CourseWithTestsSerializer

class StudentCoursesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role != 'student' or not hasattr(user, 'student_profile'):
            return Response({"detail": "Not authorized or student profile missing."}, status=403)

        courses = user.student_profile.courses.all()
        serializer = StudentCourseSerializer(courses, many=True)
        return Response(serializer.data)

class StudentActiveTestsGroupedByCourseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "student" or not hasattr(request.user, "student_profile"):
            return Response({"detail": "Not authorized."}, status=403)

        courses = request.user.student_profile.courses.all()
        serializer = CourseWithTestsSerializer(courses, many=True, context={'request': request})
        return Response(serializer.data)
