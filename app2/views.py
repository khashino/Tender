from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, FileResponse
from django.conf import settings
import os
from .models import App2User, Company, CompanyDocument
from .forms import App2UserCreationForm, App2AuthenticationForm, CompanyForm, CompanyDocumentForm
from .auth_backend import App2AuthBackend

def home(request):
    if request.user.is_authenticated and not isinstance(request.user, App2User):
        logout(request)
    return render(request, 'app2/home.html')

def login_view(request):
    if request.user.is_authenticated and isinstance(request.user, App2User):
        return redirect('app2:home')
        
    if request.method == 'POST':
        form = App2AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and isinstance(user, App2User):
                login(request, user, backend='app2.auth_backend.App2AuthBackend')
                messages.success(request, f'Welcome back, {username}!')
                return redirect('app2:home')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = App2AuthenticationForm()
    return render(request, 'app2/login.html', {'form': form})

def register(request):
    if request.user.is_authenticated and isinstance(request.user, App2User):
        return redirect('app2:home')
        
    if request.method == 'POST':
        form = App2UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='app2.auth_backend.App2AuthBackend')
            messages.success(request, 'Registration successful!')
            return redirect('app2:settings')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = App2UserCreationForm()
    return render(request, 'app2/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('app2:home')

@login_required
def settings(request):
    try:
        company = request.user.company
    except Company.DoesNotExist:
        company = None

    if request.method == 'POST':
        form = CompanyForm(request.POST, request.FILES, instance=company)
        if form.is_valid():
            company = form.save(commit=False)
            company.user = request.user
            company.save()
            messages.success(request, 'اطلاعات شرکت با موفقیت بروزرسانی شد.')
            return redirect('app2:settings')
    else:
        form = CompanyForm(instance=company)

    documents = CompanyDocument.objects.filter(company=company) if company else None
    document_form = CompanyDocumentForm()

    context = {
        'company': company,
        'form': form,
        'documents': documents,
        'document_form': document_form,
    }
    return render(request, 'app2/settings.html', context)

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = CompanyDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.company = request.user.company
            document.save()
            messages.success(request, 'سند با موفقیت آپلود شد.')
        else:
            messages.error(request, 'خطا در آپلود سند. لطفاً دوباره تلاش کنید.')
    return redirect('app2:settings')

@login_required
def delete_document(request, document_id):
    document = get_object_or_404(CompanyDocument, id=document_id, company=request.user.company)
    document.delete()
    messages.success(request, 'سند با موفقیت حذف شد.')
    return redirect('app2:settings')

@login_required
def download_document(request, document_id):
    document = get_object_or_404(CompanyDocument, id=document_id, company=request.user.company)
    
    try:
        file_path = document.file.path
        if os.path.exists(file_path):
            response = FileResponse(open(file_path, 'rb'))
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
            return response
        else:
            messages.error(request, 'فایل مورد نظر یافت نشد.')
    except Exception as e:
        messages.error(request, f'خطا در دانلود فایل: {str(e)}')
    
    return redirect('app2:settings') 