from django.core.management.base import BaseCommand
from users.models import StudentActivityAnalysis, AudioAnalysis, StudentActivityLog, TestAssignment
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Generate soft cheating and noisy legit cases for testing.'

    def handle(self, *args, **kwargs):
        test = TestAssignment.objects.filter(test__name__icontains="Mega Test").first().test
        assignments = TestAssignment.objects.filter(test=test)

        for i, a in enumerate(assignments):
            if i % 2 == 0:
                self.create_soft_cheating_case(a, a.attempt_no)
            else:
                self.create_noisy_legit_case(a, a.attempt_no)

        self.stdout.write(self.style.SUCCESS("✅ Soft cases generated."))

    def create_soft_cheating_case(self, assignment, attempt_no):
        # Exact ce aveai tu
        pass

    def create_noisy_legit_case(self, assignment, attempt_no):
        # Exact ce aveai tu
        pass
