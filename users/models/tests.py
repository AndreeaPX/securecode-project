from django.db import models
from django.conf import settings
from users.models.core import User, Course, StudentProfile, Series, Group
from users.models.questions import Question, AnswerOption
from django.core.exceptions import ValidationError
from datetime import timedelta

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
    allow_sound_analysis = models.BooleanField(default=False)
    use_proctoring = models.BooleanField(default=False)
    has_ai_assistent = models.BooleanField(default=False)
    show_result = models.BooleanField(default=False)
    maxim_points = models.IntegerField(default=90, null=False)
    extra_points = models.IntegerField(default=10, null=False)
    is_submitted = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    target_series = models.ForeignKey(Series, null=True, blank=True, on_delete=models.SET_NULL, related_name="tests_for_series")
    target_group = models.ForeignKey(Group, null=True, blank=True, on_delete=models.SET_NULL, related_name="tests_for_group")
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
        if self.target_series and self.target_group:
            raise ValidationError("Choose either a target series or a target group, not both.")
        if not self.target_series and not self.target_group:
            raise ValidationError("Test must target at least a series or a group.")
        if self.use_proctoring:
            from users.models.questions import QuestionAttachment
            has_non_image_attachment = Question.objects.filter(
                test_questions__test = self,
                attachments__isnull = False
            ).exclude(
                attachments__file__iendswith=('.png', '.jpg', '.jpeg', '.gif', '.webp')
            ).exists()
            if has_non_image_attachment:
                raise ValidationError("Proctoring is not allowed if test has downloadable (non-image) attachments.")


    def assign(self):
        filters = {}
        if self.target_series:
             filters["group__series"] = self.target_series
            
        if self.target_group:
            filters["group"] = self.target_group

        if self.target_subgroup:
            filters["subgroup"] = self.target_subgroup

        if not filters:
            raise ValidationError("Test must target at least a series or a group.")
        
        profiles = StudentProfile.objects.filter(**filters)

        created = 0
        for profile in profiles:
            _, was_created = TestAssignment.objects.get_or_create(
                test=self,
                student=profile.user
            )
            if was_created:
                created += 1

        return created

class TestQuestion(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="test_questions")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    points = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.test.name} - Q{self.order}"

class TestAssignment(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="assignments")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="assigned_tests", limit_choices_to={"role": "student"})

    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    attempt_no = models.IntegerField(default=1)
    label = models.BooleanField(null=True, blank=True)
    auto_score = models.FloatField(null=True, blank=True)
    manual_score = models.FloatField(null=True, blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_tests")

    def __str__(self):
        return f"{self.student.email} - {self.test.name} (Attempt {self.attempt_no})"

class StudentAnswer(models.Model):
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField(null=True, blank=True)
    selected_options = models.ManyToManyField(AnswerOption, blank=True)
    feedback = models.TextField(null=True, blank=True)
    needs_manual_review = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.assignment} - Q{self.question.id}"

class StudentActivityLog(models.Model):
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name="activity_logs")
    attempt_no = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    focus_lost_count = models.IntegerField(default=0)
    anomaly_score = models.FloatField(null=True, blank=True)
    event_type = models.CharField(max_length=100, null=True, blank=True)
    event_message = models.TextField(null=True, blank=True)
    pressed_key = models.CharField(max_length=10, null=True, blank=True)
    key_delay = models.FloatField(null=True, blank=True)
    def __str__(self):
        return f"{self.assignment} - Activity at {self.timestamp}"
    
class StudentActivityAnalysis(models.Model):
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name="activity_analysis")
    attempt_no = models.IntegerField(default=1)
    esc_pressed = models.IntegerField(default=0)
    second_screen_events = models.IntegerField(default=0)
    tab_switches = models.IntegerField(default=0)
    window_blurs = models.IntegerField(default=0)
    total_key_presses = models.IntegerField(default=0)
    average_key_delay = models.FloatField(null=True, blank=True)
    copy_paste_events = models.IntegerField(default=0)
    total_focus_lost = models.IntegerField(default=0)
    is_suspicious = models.BooleanField(default=False)
    analyzed_at = models.DateTimeField(auto_now=True)
    class Meta:
        unique_together = ("assignment", "attempt_no")

    def __str__(self):
        return f"Analysis for assignment {self.assignment.id}"
    
class TempFaceEventState(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE)
    attempt_no = models.IntegerField(default=1)
    event_type = models.CharField(max_length=50)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "assignment", "attempt_no", "event_type")

class AudioAnalysis(models.Model):
    assignment = models.ForeignKey(TestAssignment, on_delete=models.CASCADE, related_name="audio_analysis")
    attempt_no = models.IntegerField(default=1)
    voiced_ratio = models.FloatField()
    voiced_seconds = models.FloatField()
    mouth_open_no_voice_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("assignment", "attempt_no")

    def __str__(self):
        return f"Analysis for assignment {self.assignment.id}"