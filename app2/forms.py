from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import App2User

class App2UserCreationForm(UserCreationForm):
    class Meta:
        model = App2User
        fields = ('username', 'password1', 'password2')

class App2AuthenticationForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        if not isinstance(user, App2User):
            raise forms.ValidationError(
                "This account is not authorized to access App2.",
                code='invalid_login',
            ) 