from django.core.management.base import BaseCommand
from ai_models.trainer import train_and_save_model

class Command(BaseCommand):
    help = "Train the cheating detection model"

    def handle(self, *args, **kwargs):
        train_and_save_model()
        self.stdout.write(self.style.SUCCESS("✅ Model trained and saved!"))