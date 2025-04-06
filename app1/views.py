from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import App1User
from .forms import App1UserCreationForm, App1AuthenticationForm
from .auth_backend import App1AuthBackend
from django.contrib.auth.decorators import login_required
from app2.models import Company, CompanyDocument

def home(request):
    if request.user.is_authenticated and not isinstance(request.user, App1User):
        logout(request)
    return render(request, 'app1/home.html')

def login_view(request):
    if request.user.is_authenticated and isinstance(request.user, App1User):
        return redirect('app1:home')
        
    if request.method == 'POST':
        form = App1AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and isinstance(user, App1User):
                login(request, user, backend='app1.auth_backend.App1AuthBackend')
                messages.success(request, f'Welcome back, {username}!')
                return redirect('app1:home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = App1AuthenticationForm()
    return render(request, 'app1/login.html', {'form': form})

def register(request):
    if request.user.is_authenticated and isinstance(request.user, App1User):
        return redirect('app1:home')
        
    if request.method == 'POST':
        form = App1UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='app1.auth_backend.App1AuthBackend')
            messages.success(request, 'Registration successful!')
            return redirect('app1:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = App1UserCreationForm()
    return render(request, 'app1/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('app1:home')

@login_required
def company_approvals(request):
    # Get all unverified companies
    companies = Company.objects.filter(is_verified=False)
    return render(request, 'app1/company_approvals.html', {'companies': companies})

@login_required
def approve_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    company.is_verified = True
    company.save()
    
    # Also verify all documents
    CompanyDocument.objects.filter(company=company).update(is_verified=True)
    
    messages.success(request, f'شرکت {company.name} با موفقیت تایید شد.')
    return redirect('app1:company_approvals')

@login_required
def reject_company(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    company_name = company.name
    company.delete()
    messages.success(request, f'شرکت {company_name} با موفقیت حذف شد.')
    return redirect('app1:company_approvals') 