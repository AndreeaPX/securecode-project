from django.core.exceptions import ValidationError
import re

class CustomPasswordValidator:
    def validate(self, password, user = None):
        if len(password)<10:
            raise ValidationError("Password must be at least 10 characters!")
        if not re.search(r"[A-Z]",password):
            raise ValidationError("Password must contain at least one uppercase letter!")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValidationError("Password must contain at least one special character!")
        
    def get_help_text(self):
        return "Your password must be at least 10 characters, include one uppercase letter and one special character."