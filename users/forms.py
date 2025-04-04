from django import forms
from .models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from users.models import UserInvitation
from django.contrib.auth.hashers import check_password

class CustomUserCreationForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "role", "first_name","last_name","start_date","is_staff", "is_active", "first_login")

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("email", "role", "first_name","last_name","start_date", "is_staff", "is_active", "first_login")

class CustomLoginForm(forms.Form):
    email = forms.EmailField(label="Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Password")

    def __init__(self, *args, **kwargs):
        self.user_cache = None
        super().__init__(*args,**kwargs)

    def clean(self):

        email = self.cleaned_data.get("email")
        password = self.cleaned_data.get("password")
        
        UserInvitation.objects.filter(is_used=False, expires_at__lt=timezone.now()).delete()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError("This user does not exist.")
        
        if user.first_login:
            try:
                invitation = UserInvitation.objects.get(email=email, is_used = False)
            except UserInvitation.DoesNotExist:
                raise forms.ValidationError("This authentication code is not valid.")
            
            if invitation.is_expired():
                raise forms.ValidationError("This code has expired.")
            if invitation.failed_attempts >= 5:
                raise forms.ValidationError("Too many failed attemps. This code is not longer valid.")
            
            if not check_password(password, invitation.otp_token):
                invitation.failed_attempts += 1
                invitation.save()
                raise forms.ValidationError("Wrong code.")
            
            invitation.is_used = True
            invitation.otp_token = None
            invitation.failed_attempts = 0
            invitation.save()

            user.set_password(password)
            user.first_login = False
            user.save()

            self.user_cache = user
            return self.cleaned_data
        
        user = authenticate(email=email, password=password)
        if user is None:
            raise forms.ValidationError("Invalid email or password.")
        self.user_cache = user
        return self.cleaned_data
    
    def get_user(self):
        return self.user_cache