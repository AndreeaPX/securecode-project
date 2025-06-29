from rest_framework import serializers
from users.models.tests import StudentAnswer,TestAssignment

class StudentAnswerDetailSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)
    question_type = serializers.CharField(source="question.type", read_only=True)
    id = serializers.IntegerField()  
    correct_option_ids = serializers.SerializerMethodField()
    attachments = serializers.SerializerMethodField()
    expected_output = serializers.CharField(source="question.expected_output", read_only=True, allow_null=True)
    options = serializers.SerializerMethodField()
    max_points = serializers.SerializerMethodField()


    def get_max_points(self, obj):
        tq = obj.assignment.test.test_questions.filter(question=obj.question).first()
        return tq.points if tq else None

    class Meta:
        model = StudentAnswer
        fields = [
            "id",
            "question_text",
            "question_type",
            "attachments",
            "answer_text",       
            "selected_options",
            "feedback",             
            "correct_option_ids",
            "expected_output",
            "points",
            "options",
            "max_points",             
        ]
        read_only_fields = [
            "question_text", "question_type",
            "attachments", "correct_option_ids", "expected_output", "options","max_points",
        ]

    def get_correct_option_ids(self, obj):
        return list(obj.question.options.filter(is_correct=True).values_list("id", flat=True))

    def get_attachments(self, obj):
        request = self.context.get("request")
        return [
            {
                "url": request.build_absolute_uri(att.file.url),
                "filename": att.file.name.split("/")[-1],
                "is_image": att.file.url.lower().endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".webp")
                ),
            }
            for att in obj.question.attachments.all()
        ]
    
    def get_options(self, obj):
        return list(obj.question.options.values("id", "text"))


class AssignmentReviewSerializer(serializers.ModelSerializer):
    student_email = serializers.EmailField(source="student.email", read_only=True)
    student_name = serializers.SerializerMethodField()
    test_name = serializers.CharField(source="test.name", read_only=True)
    test_type = serializers.CharField(source="test.type", read_only=True)
    test_settings = serializers.SerializerMethodField()
    answers = StudentAnswerDetailSerializer(many=True, read_only=False)
    maxim_points = serializers.IntegerField(source="test.maxim_points", read_only=True)
    extra_points = serializers.IntegerField(source="test.extra_points", read_only=True)

    class Meta:
        model  = TestAssignment
        fields = [
            "id",
            "student_email", "student_name",
            "test_name", "test_type", "attempt_no",
            "auto_score", "manual_score",
            "test_settings",
            "answers",
            "review_comment",
            "maxim_points",
            "extra_points",  
        ]

    def get_student_name(self, obj):
        return f"{obj.student.first_name} {obj.student.last_name}".strip()

    def get_test_settings(self, obj):
        t = obj.test
        return {
            "allow_sound_analysis": t.allow_sound_analysis,
            "use_proctoring": t.use_proctoring,
            "has_ai_assistent": t.has_ai_assistent,
            "show_result": t.show_result,
        }
    
    def update(self, instance, validated_data):
        answers_data = validated_data.pop("answers", [])
        instance.review_comment = validated_data.get("review_comment", instance.review_comment)

        id_map = {a.id: a for a in instance.answers.all()}
        total_points = 0
        test = instance.test

        for ans_dict in answers_data:
            ans_obj = id_map.get(ans_dict["id"])
            if not ans_obj:
                continue

            ans_obj.feedback = ans_dict.get("feedback", ans_obj.feedback)
            if not test.show_result:
                ans_obj.points = ans_dict.get("points", ans_obj.points)
                total_points += ans_obj.points or 0
            elif "points" in ans_dict:
                raise serializers.ValidationError("Manual grading is disabled for auto-graded tests.")

            ans_obj.save()

        if not test.show_result:
            if total_points > test.maxim_points:
                raise serializers.ValidationError(
                    f"Total points ({total_points}) exceed test maximum ({test.maxim_points})."
                )
            instance.manual_score = total_points + test.extra_points

        instance.reviewed_by = self.context["request"].user
        instance.save()
        return instance
