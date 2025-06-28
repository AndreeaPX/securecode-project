from rest_framework import serializers
from users.models.tests import Test, TestAssignment

class TestSummarySerializer(serializers.ModelSerializer):
    total_assignments= serializers.IntegerField()
    finalized_count= serializers.IntegerField()

    class Meta:
        model  = Test
        fields = ["id", "name", "course", "type",
                  "start_time", "deadline",
                  "total_assignments", "finalized_count"]

class AssignmentListSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_full_name = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = TestAssignment
        fields = [
            "id", "attempt_no",
            "started_at", "finished_at",
            "auto_score", "manual_score",
            "student_email", "student_full_name",
            "status"
        ]

    def get_student_full_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}"

    def get_status(self, obj):
        return "finalized" if obj.finished_at else "in progress"
