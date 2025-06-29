from rest_framework import serializers
from users.models.tests import TestAssignment

class AssignmentProgressSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    total_assigned = serializers.IntegerField()
    finished = serializers.IntegerField()
    progress_percent = serializers.IntegerField()


class GradingProgressRowSerializer(serializers.Serializer):
    test_id = serializers.IntegerField()
    test_name = serializers.CharField()
    question_type = serializers.CharField()
    status = serializers.CharField()