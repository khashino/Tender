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
from shared_models.models import Tender
from django.utils import timezone

def home(request):
    if not request.user.is_authenticated:
        return redirect('app2:login')
    
    # Get the latest 5 tenders
    latest_tenders = Tender.objects.all().order_by('-published_date')[:5]
    
    context = {
        'latest_tenders': latest_tenders,
    }
    return render(request, 'app2/home.html', context)

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

@login_required
def tender_list(request):
    tenders = Tender.objects.all()
    return render(request, 'app2/tender_list.html', {'tenders': tenders})

@login_required
def tender_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        reference_number = request.POST.get('reference_number')
        closing_date = request.POST.get('closing_date')
        estimated_value = request.POST.get('estimated_value')
        currency = request.POST.get('currency', 'USD')
        
        try:
            tender = Tender.objects.create(
                title=title,
                description=description,
                reference_number=reference_number,
                closing_date=closing_date,
                estimated_value=estimated_value,
                currency=currency
            )
            messages.success(request, 'Tender created successfully!')
            return redirect('tender_detail', tender_id=tender.id)
        except Exception as e:
            messages.error(request, f'Error creating tender: {str(e)}')
    
    return render(request, 'app2/tender_create.html')

@login_required
def tender_detail(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    return render(request, 'app2/tender_detail.html', {'tender': tender}) 