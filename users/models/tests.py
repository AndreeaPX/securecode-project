from django.db import models
from django.conf import settings
from users.models.core import User, Course, StudentProfile
from users.models.questions import Question, AnswerOption
from django.core.exceptions import ValidationError

class Test(models.Model):
    TEST_TYPES = [
        ('exam', 'Exam'),
        ('seminar', 'Seminar'),
        ('training', 'Training')
    ]

    name = models.CharField(max_length=255, null=False, blank=True)
    type = models.CharField(max_length=20, choices=TEST_TYPES)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="tests")
    professor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={"role":"professor"})
    start_time = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=30)
    allowed_attempts = models.IntegerField(null=True, blank=True)
    allow_copy_paste = models.BooleanField(default=False)
    use_proctoring = models.BooleanField(default=False)
    has_ai_assistent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    target_series = models.CharField(max_length=10, null=True, blank=True)
    target_group = models.IntegerField(null=True, blank=True)
    target_subgroup = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def clean(self):
        if self.deadline and self.start_time and self.deadline < self.start_time:
            raise ValidationError("Deadline can not be before the start time.")
        if self.duration_minutes <= 0:
            raise ValidationError("Test duration must be > 0")
        if self.type != 'training' and self.allowed_attempts not in [1, None]:
            raise ValidationError("Only training tests can have more than one attempt.")
        
    def assign(self):
        filters = {}
        if self.target_series:
            filters["series"] = self.target_series
        if self.target_group:
            filters["group"] = self.target_group
        if self.target_subgroup:
            filters["subgroup"] = self.target_subgroup
        profiles = StudentProfile.objects.filter(**filters)
        created = 0
        for profile in profiles:
            _, was_created = TestAssignment.objects.get_or_create(
                test = self,
                student = profile.user
            )
            if was_created:
                created += 1
        return created

class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="test_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.test.name} - Q{self.order}"

class TestAssignment(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="assignments")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_tests", limit_choices_to={"role": "student"})

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    attempt_no = models.IntegerField(default=1)

    ai_score = models.FloatField(null=True, blank=True)
    manual_score = models.FloatField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_tests")

    def __str__(self):
        return f"{self.student.email} - {self.test.name} (Attempt {self.attempt_no})"

class StudentAnswer(models.Model):
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(null=True, blank=True)
    selected_options = models.ManyToManyField(AnswerOption, blank=True)
    time_spent = models.DurationField()
    ai_feedback = models.TextField(null=True, blank=True)
    needs_manual_review = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.assignment} - Q{self.question.id}"

class StudentActivityLog(models.Model):
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name="activity_logs")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    mouse_x = models.IntegerField(null=True, blank=True)
    mouse_y = models.IntegerField(null=True, blank=True)
    key_press_count = models.IntegerField(default=0)
    focus_lost_count = models.IntegerField(default=0)
    copy_paste_events = models.IntegerField(default=0)
    anomaly_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.assignment} - Activity at {self.timestamp}"