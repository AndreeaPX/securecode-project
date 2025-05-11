from rest_framework import serializers
from users.models.questions import Question, QuestionAttachment, AnswerOption

class QuestionAttachmentSerializer(serializers.ModelSerializer):
    file = serializers.FileField(required=True)
    file_type = serializers.SerializerMethodField()

    class Meta:
        model = QuestionAttachment
        fields = ["id", "file", "file_type", "uploaded_at"]

    def get_file(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url

    def get_file_type(self, obj):
        return obj.file_type()
    
    def validate_file(self, file):
        filename = file.name.lower()
        allowed_extensions = (
            '.jpg', '.jpeg', '.png', '.gif',   
            '.pdf', '.doc', '.docx', '.txt', '.zip', '.rar','xlsx',   
            '.py', '.java', '.cpp', '.c', '.js', 
            '.mp4', '.mov', '.avi', '.wmv', '.mkv', 
            '.mp3', '.wav', '.ogg', '.aac'      
        )

        if not filename.endswith(allowed_extensions):
            raise serializers.ValidationError("Unsupported file type.")

        return file
    
class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = ("id","text","is_correct")
        read_only_fields = ("id",)

class QuestionSerializer(serializers.ModelSerializer):
    attachments = QuestionAttachmentSerializer(many=True, read_only=True)
    options = AnswerOptionSerializer(many=True, required=False)
    created_by_email = serializers.CharField(source='created_by.email', read_only=True)
    created_by_full_name = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            "id", "text", "type", "course", "created_by", "created_by_email", "created_by_full_name",
            "is_shared", "is_generated_ai", "points", "attachments", "options",
            "is_code_question", "language", "starter_code", "expected_output"
        )
        read_only_fields = ("id", "created_by", "is_generated_ai")

    def get_created_by_full_name(self, obj):
        return f"{obj.created_by.first_name} {obj.created_by.last_name}"

    def create(self, validated_data):
        request = self.context.get("request")
        user = request.user
        validated_data["created_by"] = user
        options_data = validated_data.pop("options", [])
        question = Question.objects.create(**validated_data)
        for option_data in options_data:
            AnswerOption.objects.create(question=question, **option_data)
        return question

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if options_data is not None:
            instance.options.all().delete()
            for option_data in options_data:
                AnswerOption.objects.create(question=instance, **option_data)
        return instance
