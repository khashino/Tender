from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import App1User, Role, UserRole
from .forms import App1UserCreationForm, App1AuthenticationForm
from .auth_backend import App1AuthBackend
from django.contrib.auth.decorators import login_required, permission_required
from app2.models import Company, CompanyDocument
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils import timezone
from shared_models.models import TenderApplication, Tender
from django.core.files.storage import FileSystemStorage
import os
from app1.models import TenderApplicationProcess
from app1.flows import TenderApplicationFlow

def home(request):
    if request.user.is_authenticated and not isinstance(request.user, App1User):
        logout(request)
    
    # Get tender statistics
    new_tenders = Tender.objects.filter(status='published').count()
    pending_tenders = Tender.objects.filter(status='draft').count()
    approved_tenders = Tender.objects.filter(status='awarded').count()
    rejected_tenders = Tender.objects.filter(status='cancelled').count()
    
    # Get recent tenders
    recent_tenders = Tender.objects.all().order_by('-published_date')[:5]
    
    context = {
        'new_tenders': new_tenders,
        'pending_tenders': pending_tenders,
        'approved_tenders': approved_tenders,
        'rejected_tenders': rejected_tenders,
        'recent_tenders': recent_tenders
    }
    return render(request, 'app1/home.html', context)

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

@login_required
@permission_required('app1.view_role', raise_exception=True)
def role_list(request):
    roles = Role.objects.all()
    return render(request, 'app1/usersettings/role_list.html', {'roles': roles})

@login_required
@permission_required('app1.add_role', raise_exception=True)
def role_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        permission_ids = request.POST.getlist('permissions')
        
        role = Role.objects.create(
            name=name,
            description=description
        )
        role.permissions.set(permission_ids)
        
        messages.success(request, 'نقش با موفقیت ایجاد شد.')
        return redirect('app1:role_list')
    
    permissions = Permission.objects.filter(
        Q(content_type__app_label='app1') |
        Q(content_type__app_label='auth')
    )
    return render(request, 'app1/usersettings/role_create.html', {'permissions': permissions})

@login_required
@permission_required('app1.change_role', raise_exception=True)
def role_edit(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    
    if request.method == 'POST':
        role.name = request.POST.get('name')
        role.description = request.POST.get('description')
        role.permissions.set(request.POST.getlist('permissions'))
        role.save()
        
        messages.success(request, 'نقش با موفقیت ویرایش شد.')
        return redirect('app1:role_list')
    
    permissions = Permission.objects.filter(
        Q(content_type__app_label='app1') |
        Q(content_type__app_label='auth')
    )
    return render(request, 'app1/usersettings/role_edit.html', {
        'role': role,
        'permissions': permissions
    })

@login_required
@permission_required('app1.delete_role', raise_exception=True)
def role_delete(request, role_id):
    role = get_object_or_404(Role, id=role_id)
    role_name = role.name
    role.delete()
    messages.success(request, f'نقش {role_name} با موفقیت حذف شد.')
    return redirect('app1:role_list')

@login_required
@permission_required('app1.view_userrole', raise_exception=True)
def user_roles(request):
    users = App1User.objects.all()
    return render(request, 'app1/usersettings/user_roles.html', {'users': users})

@login_required
@permission_required('app1.change_userrole', raise_exception=True)
def assign_user_roles(request, user_id):
    user = get_object_or_404(App1User, id=user_id)
    
    if request.method == 'POST':
        role_ids = request.POST.getlist('roles')
        UserRole.objects.filter(user=user).delete()
        for role_id in role_ids:
            role = Role.objects.get(id=role_id)
            UserRole.objects.create(user=user, role=role)
        
        messages.success(request, 'نقش‌های کاربر با موفقیت به‌روزرسانی شدند.')
        return redirect('app1:user_roles')
    
    roles = Role.objects.all()
    user_roles = user.user_roles.values_list('role_id', flat=True)
    return render(request, 'app1/usersettings/assign_user_roles.html', {
        'user': user,
        'roles': roles,
        'user_roles': user_roles
    })

@login_required
@permission_required('app1.add_tenderapplication', raise_exception=True)
def create_tender(request):
    if request.method == 'POST':
        try:
            # Generate a unique reference number (you might want to make this more sophisticated)
            reference_number = f"TDR-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            
            # Create tender
            tender = Tender.objects.create(
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                reference_number=reference_number,
                closing_date=request.POST.get('deadline'),
                estimated_value=request.POST.get('budget'),
                currency='IRR',  # Iranian Rial
                status='published'  # Set as published by default
            )

            # Handle file uploads
            if 'documents' in request.FILES:
                fs = FileSystemStorage()
                for file in request.FILES.getlist('documents'):
                    filename = fs.save(f'tender_documents/{tender.id}/{file.name}', file)
                    # You might want to create a TenderDocument model to store these files

            messages.success(request, 'مناقصه با موفقیت ایجاد شد.')
            return redirect('app1:home')
        except Exception as e:
            messages.error(request, f'خطا در ایجاد مناقصه: {str(e)}')
            return redirect('app1:create_tender')

    return render(request, 'app1/tender/create_tender.html')

@login_required
def tender_applications(request):
    applications = TenderApplication.objects.all().order_by('-submitted_at')
    context = {
        'applications': applications,
    }
    return render(request, 'app1/tender/applications.html', context)

@login_required
def review_application(request, application_id):
    application = get_object_or_404(TenderApplication, id=application_id)
    context = {
        'application': application,
    }
    return render(request, 'app1/tender/review_application.html', context)

@login_required
def start_application_workflow(request, application_id):
    """Start the workflow for a tender application"""
    try:
        application = TenderApplication.objects.get(id=application_id)
        
        # Check if a workflow already exists for this application
        existing_process = TenderApplicationProcess.objects.filter(
            application=application
        ).exists()
        
        if existing_process:
            messages.warning(request, "A workflow already exists for this application.")
            print("A workflow already exists for this application.")
        else:
            # Start the workflow
            process = TenderApplicationFlow.start_noninteractive.run(application_id=application.id)
            messages.success(request, "Workflow started successfully.")
            print("Workflow started successfully.")
        
        return redirect('app1:tender_applications')
    
    except TenderApplication.DoesNotExist:
        print(request)
        messages.error(request, "Application not found.")
        return redirect('app1:tender_applications') 
       