from rest_framework import serializers
from users.models.tests import Test, TestQuestion
from users.serializers.questions import QuestionSerializer


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = '__all__'
        read_only_fields = ['id','created_at','professor']

class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ['id', 'test','question', 'is_required', 'order']

class TestQuestionDetailedSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()

    class Meta:
        model = TestQuestion
        fields = ['id', 'order', 'is_required', 'question']