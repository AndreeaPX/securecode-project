from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
import datetime
import logging

class UserManager(BaseUserManager):
    logger = logging.getLogger(__name__)

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not (email.endswith("@stud.ase.ro") or email.endswith(".ase.ro")):
            raise ValueError("Only ASE institutional emails are allowed")

        email = self.normalize_email(email)

        if email.endswith("@stud.ase.ro"):
            extra_fields.setdefault("role", "student")
        elif email.endswith("@admin.ase.ro"):
            extra_fields.setdefault("role", "admin")
        else:
            extra_fields.setdefault("role", "professor")

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('first_login', False)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('professor', 'Professor'),
        ('student', 'Student'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    face_encoding = models.BinaryField(null=True, blank=True)
    face_image = models.ImageField(upload_to="user_faces/", null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    first_login = models.BooleanField(default=True)
    failed_face_attempts = models.IntegerField(default=0)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100, null=True)
    start_date = models.DateField(default=datetime.date.today)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.email

class UserInvitation(models.Model):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=[('student', 'Student'), ('professor', 'Professor'), ('admin', 'Admin')])
    otp_token = models.CharField(max_length=128, null=True, blank=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    failed_attempts = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["expires_at", "is_used"]),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} ({self.role})"
    
    def is_blocked(self):
        return self.failed_attempts>=5

class Faculty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    dean = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="specializations")

    def __str__(self):
        return f"{self.name} ({self.faculty.name})"

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    is_optional = models.BooleanField(default=False)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name="courses")
    description = models.TextField(null=True, blank=True)
    is_ai_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.code} - {self.name}"

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    TYPE_CHOICES = (('b', 'Bachelor'), ('m', 'Master'), ('d', 'Doctorate'))
    group_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='b')
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name="students")
    group = models.IntegerField(default=1000)
    series = models.CharField(max_length=10, null=True, blank=True)
    subgroup = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)], default=1)
    start_year = models.IntegerField(default=datetime.date.today().year)
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return f"{self.user.email} - Y{self.year} - Gr{self.group}"

class ProfessorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proffesor_profile')
    teaches_lecture = models.BooleanField(default=False)
    teaches_seminar = models.BooleanField(default=False)
    specialization = models.ForeignKey(Specialization, on_delete=models.CASCADE, related_name="professors")
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return self.user.email
