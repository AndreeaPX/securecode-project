from django.db import models
from django.conf import settings
from users.models.core import Course, User
from django.core.exceptions import ValidationError
from django.db.models.signals import post_delete
from django.dispatch import receiver

class Question(models.Model):
    QUESTION_TYPES=[
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
        ('open', 'Open Answer'),
        ('code','Code Response')
    ]

    LANGUAGE_CHOICES =[
        ('python','Python'),
        ('java','Java'),
        ('c','C'),
        ('cpp','C++'),
        ('javascript','JavaScript'),
        ('sql','SQL'),
        ('other','Other')
    ]

    text = models.TextField(blank=True, null=False)
    type = models.CharField(max_length=10, choices=QUESTION_TYPES)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="questions")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="questions")
    is_shared = models.BooleanField(default=False)
    is_generated_ai = models.BooleanField(default=False)
    is_code_question = models.BooleanField(default=False)
    starter_code = models.TextField(blank = True, null = True, help_text="Starter code for coding question.")
    language = models.CharField(max_length=20,choices=LANGUAGE_CHOICES, blank=True, null=True)
    expected_output = models.TextField(blank=True, null=True, help_text="Expected output after running the code.")
    created_at = models.DateTimeField(auto_now_add=True)
    points = models.PositiveIntegerField(default=1, help_text="Number of points this question is worth.")

    def __str__(self):
        return f" {self.text[:50]}"
    
    def clean(self):
        if self.pk:
            options = AnswerOption.objects.filter(question = self)
            correct_count = options.filter(is_correct = True).count()

            if self.type == 'single' and correct_count!=1:
                raise ValidationError("Single choice questions must have exactly one correct answer.")
            elif self.type == 'multiple' and correct_count < 1:
                raise ValidationError("Multiple choice questions must have at least one correct answer.")
            

class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="options"  
    )
    text = models.CharField(max_length=512, null=False, blank=True)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Option for Q{self.question.id}: {self.text[:30]}"
    
    class Meta:
        unique_together = ('question', 'text')
            
class QuestionAttachment(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(upload_to="attachments/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def file_type(self):
        filename = self.file.name.lower()
        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            return 'image'
        elif filename.endswith(('.pdf', '.doc', '.docx', '.txt', '.zip', '.rar', '.xlsx')):
            return 'document'
        elif filename.endswith(('.py', '.java', '.cpp', '.c', '.js')):
            return 'code'
        elif filename.endswith(('.mp4', '.mov', '.avi', '.wmv', '.mkv')):
            return 'video'
        elif filename.endswith(('.mp3', '.wav', '.ogg', '.aac')):
            return 'audio'
        else:
            return 'unknown'
        
@receiver(post_delete, sender=QuestionAttachment)
def delete_attachment_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(False)