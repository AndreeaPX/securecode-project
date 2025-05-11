from django.core.management.base import BaseCommand
from users.models.core import User, StudentProfile, Group, Course
import csv
import datetime
import random
from pathlib import Path

class Command(BaseCommand):
    help = "Assigns StudentProfiles randomly to existing student users from student_otps.csv"

    def handle(self, *args, **options):
        csv_path = Path("student_otps.csv")
        if not csv_path.exists():
            self.stderr.write("❌ student_otps.csv not found.")
            return

        groups = list(Group.objects.select_related("series__specialization").all())
        if not groups:
            self.stderr.write("❌ No groups found in database.")
            return

        created = 0
        skipped = 0

        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                email = row["email"].strip().lower()

                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    self.stderr.write(f"❌ User not found: {email}")
                    continue

                if hasattr(user, "student_profile"):
                    self.stdout.write(f"⚠️ Skipping (already has profile): {email}")
                    skipped += 1
                    continue

                # Pick random group and extract series/specialization info
                group = random.choice(groups)
                series = group.series
                specialization = series.specialization
                year = series.year
                group_type = series.group_type
                subgroup = random.choice([1, 2])

                # Get matching courses
                courses = Course.objects.filter(specialization=specialization, year=year)

                profile = StudentProfile.objects.create(
                    user=user,
                    group_type=group_type,
                    year=year,
                    specialization=specialization,
                    group=group,
                    subgroup=subgroup,
                    start_year=datetime.date.today().year,
                )
                profile.courses.set(courses)

                self.stdout.write(self.style.SUCCESS(
                    f"✅ {email} → Group {group.number}, Series {series.name} (Y{year}, {group_type}), Subgroup {subgroup}"
                ))
                created += 1

        self.stdout.write(f"\n🎓 Done. Created: {created}, Skipped: {skipped}")
