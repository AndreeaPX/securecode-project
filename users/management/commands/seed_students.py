from django.core.management.base import BaseCommand
from django.utils.crypto import get_random_string
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from users.models.core import User, UserInvitation
import random
import datetime
import csv
from pathlib import Path

FIRST_NAMES = ["Ana", "Mihai", "Irina", "Andrei", "Cristina", "David", "Roxana", "Alex", "Laura", "Vlad",
               "Bianca", "George", "Alina", "Cosmin", "Denisa", "Florin", "Oana", "Teodor", "Elena", "Razvan"]
LAST_NAMES = ["Popescu", "Ionescu", "Matei", "Georgescu", "Stan", "Marin", "Ilie", "Popa", "Enache", "Dragomir",
              "Neagu", "Radu", "Voicu", "Tudor", "Serban", "Ghita", "Mocanu", "Nita", "Stefan", "Petrescu"]

class Command(BaseCommand):
    help = "Seeds 40 student users with OTPs and links them to panaandreea@admin.ase.ro"

    def handle(self, *args, **options):
        try:
            admin_user = User.objects.get(email="panaandreea@admin.ase.ro")
        except User.DoesNotExist:
            self.stderr.write("❌ Admin user 'panaandreea@admin.ase.ro' not found. Aborting.")
            return

        otp_dump = []
        created_count = 0

        for i in range(1, 41):
            fn = random.choice(FIRST_NAMES)
            ln = random.choice(LAST_NAMES)
            email = f"{fn.lower()}.{ln.lower()}{i:02d}@stud.ase.ro"

            if User.objects.filter(email=email).exists():
                self.stdout.write(f"⚠️ Skipping existing user: {email}")
                continue

            # Create the student user
            user = User.objects.create(
                email=email,
                first_name=fn,
                last_name=ln,
                role="student",
                is_active=True,
                is_staff=False,
                start_date=datetime.date.today()
            )
            user.set_unusable_password()
            user.save()

            # Generate and hash OTP
            otp_token = get_random_string(length=32)
            otp_hash = make_password(otp_token)

            # Create invitation
            UserInvitation.objects.create(
                email=email,
                role="student",
                otp_token=otp_hash,
                is_used=False,
                expires_at=timezone.now() + datetime.timedelta(hours=24),
                invited_by=admin_user
            )

            # Save OTP for output
            otp_dump.append((email, otp_token))
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f"✅ Created: {email} | OTP: {otp_token}"))

        # Write OTPs to CSV
        if otp_dump:
            csv_path = Path("student_otps.csv")
            with open(csv_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["email", "otp_token"])
                writer.writerows(otp_dump)

            self.stdout.write(self.style.WARNING(f"\n📁 OTPs saved to: {csv_path.resolve()}"))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Done! {created_count} students created."))
