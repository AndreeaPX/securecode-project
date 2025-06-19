from rest_framework import serializers
from users.models.core import Course
from users.models.questions import Question, AnswerOption
from users.models.tests import TestAssignment, StudentAnswer, StudentActivityLog
from django.utils.dateparse import parse_duration
from django.utils import timezone
from ai_models.evaluation_engine import evaluate_assignment

class StudentCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name", "year", "semester"]

class AnswerItemSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer_text = serializers.CharField(allow_blank = True, required = False)
    selected_option_ids = serializers.ListField(child = serializers.IntegerField(),required = False)
    #time_spent = serializers.CharField(required=False)

class SubmitAnswersSerializer(serializers.Serializer):
    assignment_id = serializers.IntegerField()
    answers = AnswerItemSerializer(many = True)

    def validate(self, data):
        request = self.context["request"]   
        user = request.user

        try:
            assignment = TestAssignment.objects.select_related("test").get(
                id=data["assignment_id"], student=user
            )
        except TestAssignment.DoesNotExist:
            raise serializers.ValidationError("Invalid assignment. It does not exist.")

        test = assignment.test

        if assignment.finished_at and test.type != "training":
            raise serializers.ValidationError("This attempt has already been submitted.")

        if test.type == "training" and test.allowed_attempts is not None:
            if assignment.attempt_no >= test.allowed_attempts:
                raise serializers.ValidationError("You have used all allowed attempts.")

        data["assignment"] = assignment
        return data



    def create(self, validated_data):
        assignment = validated_data["assignment"]
        test = assignment.test

        if test.type == "training":
            assignment.answers.all().delete()
            StudentActivityLog.objects.filter(assignment=assignment, attempt_no__lt = assignment.attempt_no).delete()
            assignment.attempt_no += 1
            
            assignment.finished_at = timezone.now()
            assignment.save()

        elif assignment.finished_at:
            return {"status": "already_submitted"}

        for item in validated_data["answers"]:
            question = Question.objects.get(id=item["question_id"])
            answer = StudentAnswer.objects.create(
                assignment=assignment,
                question=question,
                answer_text=item.get("answer_text"),
                #time_spent=parse_duration(item.get("time_spent", "0:00:00")),
                needs_manual_review=question.type in ["open", "code"]
            )
            if question.type in ["single", "multiple"]:
                options = AnswerOption.objects.filter(id__in=item.get("selected_option_ids", []), question=question)
                answer.selected_options.set(options)

        assignment.finished_at = timezone.now()
        if test.show_result:
            answers = assignment.answers.select_related("question").prefetch_related("selected_options")
            all_questions = all(ans.question.type in ["single","multiple"] for ans in answers)
            if all_questions:
                total_score = 0
                total_points = test.maxim_points + test.extra_points
                value_per_q = total_points / answers.count() if answers.count() else 0

                for ans in answers:
                    correct_ids = set(ans.question.options.filter(is_correct=True).values_list("id", flat=True))
                    selected_ids = set(ans.selected_options.values_list("id", flat=True))

                    if ans.question.type == "single":
                        if selected_ids == correct_ids:
                            total_score+=value_per_q
                    elif ans.question.type == "multiple":
                        if selected_ids == correct_ids:
                            total_score+=value_per_q
                        elif selected_ids and selected_ids.issubset(correct_ids):
                            partial = value_per_q * (len(selected_ids) / len(correct_ids))
                            total_score += partial
                        elif selected_ids.intersection(correct_ids) and not selected_ids.issubset(correct_ids):
                            pass
                        else:
                            pass
                assignment.auto_score = round(total_score,2)
        assignment.save()
        
        if test.has_ai_assistent:
            evaluate_assignment(assignment)

        return {
            "status": "submitted",
            "finished_at": assignment.finished_at,
            "attempt_no": assignment.attempt_no,
            "allowed_attempts": test.allowed_attempts,
            "auto_score": assignment.auto_score if test.show_result else None,
        }

