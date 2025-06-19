from django.db import models
from django.contrib.auth import get_user_model
from users.models import ProfessorProfile

User = get_user_model()

class AttentionReport(models.Model):
    session_id     = models.CharField(max_length=64, unique=True)
    professor      = models.ForeignKey(ProfessorProfile, on_delete=models.CASCADE, related_name="attention_reports")
    created_by     = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at     = models.DateTimeField(auto_now_add=True)

    avg_attention  = models.FloatField()
    raw_timeline   = models.JSONField()
    advice         = models.JSONField()

    pdf_file     = models.FileField(upload_to="attention_reports/", null=True, blank=True)
    def __str__(self):
        return f"Report {self.session_id} – {self.professor.user.full_name}"
