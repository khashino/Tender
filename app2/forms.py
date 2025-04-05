from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import App2User, Company, CompanyDocument

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

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = [
            'name', 'registration_number', 'economic_code', 'national_id',
            'phone', 'address', 'website', 'description', 'logo'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-control'}),
            'economic_code': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CompanyDocumentForm(forms.ModelForm):
    class Meta:
        model = CompanyDocument
        fields = ['document_type', 'file', 'description']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        } 