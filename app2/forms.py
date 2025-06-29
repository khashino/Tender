from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import App2User, Company, CompanyDocument
from shared_models.models import TenderApplication

class App2UserCreationForm(UserCreationForm):
    class Meta:
        model = App2User
        fields = ('username', 'password1', 'password2')

class OracleUserRegistrationForm(forms.Form):
    """Form for registering users in Oracle KRN_USER_DETAIL table"""
    
    # Basic user information
    name = forms.CharField(
        max_length=100,
        label='نام',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام خود را وارد کنید',
            'required': True
        })
    )
    
    family = forms.CharField(
        max_length=100,
        label='نام خانوادگی',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام خانوادگی خود را وارد کنید',
            'required': True
        })
    )
    
    user_name = forms.CharField(
        max_length=255,
        label='نام کاربری',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'نام کاربری خود را وارد کنید',
            'required': True
        })
    )
    
    password = forms.CharField(
        max_length=255,
        label='رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را وارد کنید',
            'required': True
        })
    )
    
    password_confirm = forms.CharField(
        max_length=255,
        label='تکرار رمز عبور',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'رمز عبور خود را مجدداً وارد کنید',
            'required': True
        })
    )
    
    phone_number = forms.CharField(
        max_length=20,
        label='شماره تماس',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'شماره تماس خود را وارد کنید'
        })
    )
    
    address = forms.CharField(
        max_length=255,
        label='آدرس',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'آدرس خود را وارد کنید'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError('رمزهای عبور مطابقت ندارند.')
        
        return cleaned_data
    
    def clean_user_name(self):
        user_name = self.cleaned_data.get('user_name')
        if user_name:
            # Check if username already exists in Oracle
            from .oracle_utils import execute_oracle_query
            try:
                query = "SELECT COUNT(*) as count FROM KRN_USER_DETAIL WHERE UPPER(user_name) = UPPER(%s)"
                result = execute_oracle_query(query, [user_name])
                if result and result[0]['COUNT'] > 0:
                    raise forms.ValidationError('این نام کاربری قبلاً استفاده شده است.')
            except Exception as e:
                # If we can't check, allow it to proceed
                pass
        return user_name

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

class TenderApplicationForm(forms.ModelForm):
    class Meta:
        model = TenderApplication
        fields = ['cover_letter', 'price_quote', 'proposal_document', 'additional_document']
        widgets = {
            'cover_letter': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price_quote': forms.NumberInput(attrs={'class': 'form-control'}),
            'proposal_document': forms.FileInput(attrs={'class': 'form-control'}),
            'additional_document': forms.FileInput(attrs={'class': 'form-control'}),
        } 