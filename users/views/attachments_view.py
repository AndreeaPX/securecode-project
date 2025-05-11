from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from users.models.questions import Question, QuestionAttachment
from users.serializers.questions import QuestionAttachmentSerializer

class QuestionAttachmentAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, question_id):
        try:
            question = Question.objects.get(id=question_id, created_by=request.user)
        except Question.DoesNotExist:
            return Response({"error": "Question not found or access denied."}, status=404)
        
        serializer = QuestionAttachmentSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            attachment = serializer.save(question=question)
            print("Uploaded file path:", attachment.file.path)
            print("Uploaded file URL:", attachment.file.url)

            response_serializer = QuestionAttachmentSerializer(attachment, context={'request': request})
            return Response(response_serializer.data, status=201)

        else:
            return Response(serializer.errors, status=400)
