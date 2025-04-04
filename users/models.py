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
        try:
            if not email:
                raise ValueError("Email is required")
            email = self.normalize_email(email) #trim + lowecase
            user = self.model(email=email, **extra_fields)
            user.set_password(password) #PBKDF2 with SHA256  -> random salt  260,000+ by default (as of Django 5.x)
            user.save()
            return user
        except Exception as e:
            self.logger.error(f"[create_user] Failed: {str(e)}")
            raise

    def create_superuser(self, email, password=None, **extra_fields):
        try:
            extra_fields.setdefault('is_staff', True)
            extra_fields.setdefault('is_superuser', True)
            extra_fields.setdefault('first_login', False)  
            return self.create_user(email, password, **extra_fields)
        except Exception as e:
            self.logger.error(f"[create_superuser] Failed: {str(e)}")
            raise

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('professor', 'Professor'),
        ('student', 'Student'),
    )

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    face_encoding = models.BinaryField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    first_login = models.BooleanField(default=True)

    #extra
    first_name = models.TextField(null = True)
    last_name = models.TextField(null = True)
    start_date = models.DateField(default=datetime.date.today)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.email.endswith("@stud.ase.ro"):
            self.role = "student"
        elif self.email.endswith(".ase.ro") and not self.email.endswith("@admin.ase.ro"):
            self.role = "professor"
        elif self.email.endswith("@admin.ase.ro"):
            self.role = "admin"
        else:
            raise ValueError("Only ASE institutional emails are allowed")
    
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

class UserInvitation(models.Model):
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=50, choices=[('student', 'Student'), ('professor', 'Professor'), ('admin', 'Admin')])
    otp_token = models.CharField(max_length=128,null=True, blank=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    failed_attempts = models.IntegerField(default=0)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.email} ({self.role})"
    

class Faculty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

class Specialization(models.Model):
    name = models.CharField(max_length=100, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name="specializations")
    def __str__(self):
        return f"{self.name} ({self.faculty.name})"

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    semester = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(2)])
    is_optional = models.BooleanField(default=False)
    specialization = models.ForeignKey(
        Specialization, on_delete=models.CASCADE, related_name="courses"
    )

    filter_key = models.CharField(max_length=100, editable=False)
    def save(self, *args, **kwargs):
        self.filter_key = f"{self.year}_{self.specialization.id}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code} - {self.name}"

class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student_profile')
    TYPE_CHOICES = (('b', 'Bachelor'),('m', 'Master'),('d', 'Doctorate'))
    group_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default='b')
    group = models.IntegerField(default=1000)
    year = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    specialization = models.ForeignKey(
        Specialization, on_delete=models.CASCADE, related_name="students"
    )
    courses = models.ManyToManyField(Course)

    def __str__(self):
        return self.user.email

class ProfessorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='proffesor_profile')
    teaches_lecture = models.BooleanField(default=False)
    teaches_seminar = models.BooleanField(default=False)
    specialization = models.ForeignKey(
        Specialization, on_delete=models.CASCADE, related_name="professors"
    )
    courses = models.ManyToManyField(Course)
    def __str__(self):
        return self.user.email

