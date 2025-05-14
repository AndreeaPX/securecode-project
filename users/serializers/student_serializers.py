from rest_framework import serializers
from users.models.core import Course

class StudentCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name", "year", "semester"]