from rest_framework import serializers
from users.models.tests import TestAssignment, StudentAnswer

class StudentAnswerSerializer(serializers.ModelSerializer):
    selected_option_ids = serializers.SerializerMethodField()

    class Meta:
        model = StudentAnswer
        fields = ["question_id", "answer_text", "selected_option_ids"]

    def get_selected_option_ids(self, obj):
        return list(obj.selected_options.values_list("id", flat=True))


class ProfessorAssignmentSerializer(serializers.ModelSerializer):
    answers = StudentAnswerSerializer(many=True, read_only=True)
    report_url = serializers.SerializerMethodField()
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = TestAssignment
        fields = [
            "id",
            "student_name",
            "attempt_no",
            "auto_score",
            "ai_cheating",
            "ai_probability",
            "report_url",
            "answers",
        ]

    def get_report_url(self, obj):
        if obj.test.has_ai_assistent and obj.report_pdf:
            return obj.report_pdf.url
        return None

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip() or obj.student.email
