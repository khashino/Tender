from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import App1User

class App1UserCreationForm(UserCreationForm):
    class Meta:
        model = App1User
        fields = ('username', 'password1', 'password2')

class App1AuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not isinstance(user, App1User):
            raise forms.ValidationError(
                "This account is not authorized to access App1.",
                code='invalid_login',
            ) 