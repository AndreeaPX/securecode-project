from rest_framework import serializers
from users.models.tests import Test, TestQuestion, TestAssignment
from users.serializers.questions import QuestionSerializer
from users.models.core import Series, Group, Course
from django.utils import timezone


class TestSerializer(serializers.ModelSerializer):
    target_series = serializers.PrimaryKeyRelatedField(
        queryset=Series.objects.all(), required=False, allow_null=True
    )
    target_group = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Test
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'professor']

    def validate(self, data):
        target_series = data.get("target_series")
        target_group = data.get("target_group")
        target_subgroup = data.get("target_subgroup")
        test_type = data.get("type")

        if target_series and target_group:
            raise serializers.ValidationError("Select either a series or a group, not both.")

        if not target_series and not target_group:
            raise serializers.ValidationError("You must assign the test to a series or a group.")

        if test_type == "exam" and not target_series:
            raise serializers.ValidationError("Exam must target a series.")

        if test_type == "seminar" and not target_group:
            raise serializers.ValidationError("Seminar must target a group.")

        if test_type == "training" and not (target_series or target_group):
            raise serializers.ValidationError("Training must target at least a group or series.")
        
        if test_type != "exam":
            if target_group:
                if target_subgroup is not None and target_subgroup not in [1, 2]:
                    raise serializers.ValidationError("Subgroup must be 1 or 2.")
            elif target_subgroup is not None:
                raise serializers.ValidationError("Subgroups can only be used with groups.")
        elif target_subgroup is not None:
            raise serializers.ValidationError("Exams cannot have a subgroup.")

        return data
    
class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ['id', 'test','question', 'is_required', 'order']

class TestQuestionDetailedSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()

    class Meta:
        model = TestQuestion
        fields = ['id', 'order', 'is_required', 'question']

class TestAssignmentSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source = 'student.email', read_only = True)
    test_name = serializers.CharField(source="test.name", read_only=True)
    course_name = serializers.CharField(source="test.course.name", read_only=True)
    allowed_attempts = serializers.IntegerField(source='test.allowed_attempts', read_only = True)
    test = TestSerializer(read_only=True) 
    
    class Meta:
        model = TestAssignment
        fields = [
            "id", "test", "test_name", "course_name",
            "student", "student_email",
            "started_at", "finished_at", "attempt_no",
            "auto_score", "manual_score", "reviewed_by","allowed_attempts"
        ]
        read_only_fields = ["id", "student_email", "test_name", "course_name"]



class CourseWithTestsSerializer(serializers.ModelSerializer):
    tests = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'tests']

    def get_tests(self, course):
        student = self.context['request'].user

        assignments = TestAssignment.objects.filter(
            student=student,
            test__course=course
        ).select_related('test', 'test__course')

        return TestAssignmentSerializer(assignments, many=True).data