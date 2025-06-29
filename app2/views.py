from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, FileResponse, JsonResponse
from django.conf import settings
import os
from .models import App2User, Company, CompanyDocument, Announcement, LatestNews, Notification, Message
from .forms import App2UserCreationForm, App2AuthenticationForm, CompanyForm, CompanyDocumentForm, OracleUserRegistrationForm, OracleVendorForm
from .auth_backend import App2AuthBackend, OracleUser
from .oracle_utils import execute_oracle_query, test_oracle_connection, get_oracle_tables, get_oracle_table_info, create_oracle_user, create_vendor, update_user_vendor_id, get_vendor_by_id
# from shared_models.models import Tender, TenderApplication  # Commented out to remove dependency
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json

def home(request):
    #if not request.user.is_authenticated:
    #    return redirect('app2:login')
    
    # Get the latest announcements, news and tenders
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    latest_news = LatestNews.objects.filter(is_active=True).order_by('-created_at')[:5]
    # latest_tenders = Tender.objects.all().order_by('-published_date')[:5]  # Commented out due to dependency
    
    context = {
        'announcements': announcements,
        'latest_news': latest_news,
        # 'latest_tenders': latest_tenders,  # Commented out due to dependency
    }
    return render(request, 'app2/home.html', context)

def login_view(request):
    # Clear any existing session data to prevent conflicts
    if hasattr(request, 'session'):
        request.session.flush()
    
    # Check if user is already authenticated (Oracle or Django user)
    if request.user.is_authenticated:
        return redirect('app2:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            # Authenticate using Oracle backend
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Handle Oracle user login manually to ensure correct session data
                if isinstance(user, OracleUser):
                    # Store the correct session data for OracleUser
                    from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
                    
                    # Clear any existing session data
                    request.session.flush()
                    
                    # Store the user ID (integer) and backend path
                    request.session[SESSION_KEY] = user.pk  # This should be an integer
                    request.session[BACKEND_SESSION_KEY] = 'app2.auth_backend.OracleAuthBackend'
                    request.session[HASH_SESSION_KEY] = user.get_session_auth_hash()
                    
                    # Ensure session is saved
                    request.session.save()
                    
                    # Set the user on the request
                    request.user = user
                    
                    welcome_name = user.get_full_name() or user.username
                    messages.success(request, f'خوش آمدید، {welcome_name}!')
                else:
                    # Use standard Django login for regular users
                    login(request, user)
                    messages.success(request, f'خوش آمدید، {username}!')
                
                # Redirect to next page or home
                next_url = request.GET.get('next', 'app2:home')
                return redirect(next_url)
            else:
                messages.error(request, 'نام کاربری یا رمز عبور اشتباه است.')
        else:
            messages.error(request, 'لطفاً نام کاربری و رمز عبور را وارد کنید.')
    
    return render(request, 'app2/login.html')

def register(request):
    """Oracle user registration view"""
    if request.user.is_authenticated:
        return redirect('app2:home')
        
    if request.method == 'POST':
        form = OracleUserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                # Prepare user data for Oracle insertion
                user_data = {
                    'name': form.cleaned_data['name'],
                    'family': form.cleaned_data['family'],
                    'user_name': form.cleaned_data['user_name'],
                    'password': form.cleaned_data['password'],
                    'phone_number': form.cleaned_data.get('phone_number'),
                    'address': form.cleaned_data.get('address'),
                    'group_id': 1,  # Default group ID
                    'vendor_id': None  # Default vendor ID (null)
                }
                
                # Create user in Oracle database
                created_user_data = create_oracle_user(user_data)
                
                if created_user_data:
                    # Create OracleUser instance
                    oracle_user = OracleUser(created_user_data)
                    
                    # Log the user in manually (similar to login view)
                    from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY, HASH_SESSION_KEY
                    
                    # Clear any existing session data
                    request.session.flush()
                    
                    # Store the user ID (integer) and backend path
                    request.session[SESSION_KEY] = oracle_user.pk
                    request.session[BACKEND_SESSION_KEY] = 'app2.auth_backend.OracleAuthBackend'
                    request.session[HASH_SESSION_KEY] = oracle_user.get_session_auth_hash()
                    
                    # Ensure session is saved
                    request.session.save()
                    
                    # Set the user on the request
                    request.user = oracle_user
                    
                    messages.success(request, f'ثبت‌نام با موفقیت انجام شد! خوش آمدید، {oracle_user.get_full_name()}!')
                    return redirect('app2:home')
                else:
                    messages.error(request, 'خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.')
                    
            except Exception as e:
                messages.error(request, f'خطا در ثبت‌نام: {str(e)}')
        else:
            messages.error(request, 'لطفاً خطاهای فرم را اصلاح کنید.')
    else:
        form = OracleUserRegistrationForm()
    
    return render(request, 'app2/register.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'شما با موفقیت خارج شدید.')
    return redirect('app2:login')

@login_required
def settings(request):
    """Settings view that works with both Django users and Oracle users"""
    
    # Check if user is Oracle user or Django user
    if isinstance(request.user, OracleUser):
        # Handle Oracle user with vendor/company information
        return oracle_user_settings(request)
    else:
        # Handle Django user with Company model (existing functionality)
        return django_user_settings(request)

def oracle_user_settings(request):
    """Settings for Oracle users with vendor/company management"""
    user = request.user
    company = user.company  # This will fetch from KRNR_VENDOR table
    
    if request.method == 'POST':
        # Determine if we're creating a new vendor or updating existing one
        vendor_data = None
        if company and company.vendor_id:
            # Get existing vendor data for form initialization
            vendor_data = get_vendor_by_id(company.vendor_id)
        
        form = OracleVendorForm(request.POST, vendor_data=vendor_data)
        if form.is_valid():
            try:
                vendor_info = {
                    'vendor_name': form.cleaned_data['vendor_name'],
                    'registration_number': form.cleaned_data.get('registration_number'),
                    'address': form.cleaned_data.get('address'),
                    'email': form.cleaned_data.get('email'),
                    'phone_number': form.cleaned_data.get('phone_number')
                }
                
                if company and company.vendor_id:
                    # Update existing vendor
                    update_query = """
                    UPDATE KRNR_VENDOR 
                    SET VENDOR_NAME = %s,
                        REGISTRATION_NUMBER = %s,
                        ADDRESS = %s,
                        EMAIL = %s,
                        PHONE_NUMBER = %s
                    WHERE VENDOR_ID = %s
                    """
                    
                    params = [
                        vendor_info['vendor_name'],
                        vendor_info['registration_number'],
                        vendor_info['address'],
                        vendor_info['email'],
                        vendor_info['phone_number'],
                        company.vendor_id
                    ]
                    
                    execute_oracle_query(update_query, params)
                    messages.success(request, 'اطلاعات شرکت با موفقیت بروزرسانی شد.')
                else:
                    # Create new vendor
                    created_vendor = create_vendor(vendor_info)
                    if created_vendor:
                        # Update user's vendor_id
                        vendor_id = created_vendor['VENDOR_ID']
                        if update_user_vendor_id(user.user_id, vendor_id):
                            # Refresh user's company data
                            user._company = None
                            user._company_loaded = False
                            messages.success(request, 'اطلاعات شرکت با موفقیت ایجاد شد.')
                        else:
                            messages.error(request, 'خطا در اتصال شرکت به کاربر.')
                    else:
                        messages.error(request, 'خطا در ایجاد شرکت.')
                
                return redirect('app2:settings')
                
            except Exception as e:
                messages.error(request, f'خطا در ذخیره اطلاعات شرکت: {str(e)}')
    else:
        # Initialize form with existing vendor data if available
        vendor_data = None
        if company and company.vendor_id:
            vendor_data = get_vendor_by_id(company.vendor_id)
        
        form = OracleVendorForm(vendor_data=vendor_data)

    context = {
        'user': user,
        'company': company,
        'form': form,
        'is_oracle_user': True,
    }
    return render(request, 'app2/oracle_settings.html', context)

def django_user_settings(request):
    """Settings for Django users with Company model (existing functionality)"""
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
        'is_oracle_user': False,
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
    tenders = Tender.objects.all().order_by('-published_date')
    context = {
        'tenders': tenders,
    }
    return render(request, 'app2/tender/tender_list.html', context)

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
    return render(request, 'app2/tender/tender_detail.html', {'tender': tender})

@login_required
def apply_to_tender(request, tender_id):
    tender = get_object_or_404(Tender, id=tender_id)
    company = request.user.company
    
    # Check if tender is still open
    if tender.status != 'published':
        messages.error(request, 'This tender is no longer accepting applications.')
        return redirect('app2:tender_list')
    
    # Check if company has already applied
    if TenderApplication.objects.filter(tender=tender, applicant=company).exists():
        messages.error(request, 'You have already applied to this tender.')
        return redirect('app2:tender_list')
    
    if request.method == 'POST':
        form = TenderApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.tender = tender
            application.applicant = company
            application.save()
            
            # Note: TenderApplicationFlow from app1 has been removed
            # Application submitted successfully without workflow integration
            
            messages.success(request, 'Your application has been submitted successfully!')
            return redirect('app2:tender_list')
    else:
        form = TenderApplicationForm()
    
    context = {
        'tender': tender,
        'form': form,
    }
    return render(request, 'app2/tender/apply_to_tender.html', context)

@login_required
def my_applications(request):
    """View for 'پیشنهادات من' (My Proposals) to show user's tender applications and their status."""
    # Get the company associated with the current user
    try:
        company = request.user.company
        # Get all applications submitted by this company
        applications = TenderApplication.objects.filter(applicant=company).order_by('-submitted_at')
        
        # Note: TenderApplicationProcess from app1 has been removed
        # Applications will show without process information
        
    except Exception as e:
        messages.error(request, f'Error retrieving your applications: {str(e)}')
        applications = []
    
    context = {
        'applications': applications,
    }
    return render(request, 'app2/tender/my_applications.html', context)

def news_announcements(request):
    announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')
    latest_news = LatestNews.objects.filter(is_active=True).order_by('-created_at')
    
    context = {
        'announcements': announcements,
        'latest_news': latest_news,
    }
    return render(request, 'app2/news_announcements.html', context)

def rules(request):
    return render(request, 'app2/rules.html')

def faq(request):
    return render(request, 'app2/faq.html')

def help(request):
    return render(request, 'app2/help.html')

@login_required
def oracle_dashboard(request):
    """Oracle database dashboard view."""
    context = {
        'page_title': 'Oracle Database Dashboard'
    }
    return render(request, 'app2/oracle/dashboard.html', context)

@login_required
def oracle_test_connection(request):
    """Test Oracle database connection."""
    try:
        is_connected = test_oracle_connection()
        if is_connected:
            messages.success(request, 'Oracle database connection successful!')
        else:
            messages.error(request, 'Oracle database connection failed!')
    except Exception as e:
        messages.error(request, f'Error testing Oracle connection: {str(e)}')
    
    return redirect('app2:oracle_dashboard')

@login_required
def oracle_tables(request):
    """List all Oracle tables."""
    try:
        tables = get_oracle_tables()
        context = {
            'tables': tables,
            'page_title': 'Oracle Tables'
        }
        return render(request, 'app2/oracle/tables.html', context)
    except Exception as e:
        messages.error(request, f'Error retrieving Oracle tables: {str(e)}')
        return redirect('app2:oracle_dashboard')

@login_required
def oracle_table_info(request, table_name):
    """Get detailed information about a specific Oracle table."""
    try:
        table_info = get_oracle_table_info(table_name)
        context = {
            'table_name': table_name,
            'table_info': table_info,
            'page_title': f'Table Info: {table_name}'
        }
        return render(request, 'app2/oracle/table_info.html', context)
    except Exception as e:
        messages.error(request, f'Error retrieving table info for {table_name}: {str(e)}')
        return redirect('app2:oracle_tables')

@login_required
def oracle_query_interface(request):
    """Interface for executing custom Oracle queries."""
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if query:
            try:
                # Only allow SELECT queries for security
                if not query.upper().startswith('SELECT'):
                    messages.error(request, 'Only SELECT queries are allowed for security reasons.')
                    return render(request, 'app2/oracle/query_interface.html', {'query': query})
                
                results = execute_oracle_query(query)
                context = {
                    'query': query,
                    'results': results,
                    'page_title': 'Oracle Query Results'
                }
                return render(request, 'app2/oracle/query_results.html', context)
            except Exception as e:
                messages.error(request, f'Error executing query: {str(e)}')
                return render(request, 'app2/oracle/query_interface.html', {'query': query})
        else:
            messages.error(request, 'Please enter a query.')
    
    return render(request, 'app2/oracle/query_interface.html')

@login_required
@require_http_methods(["POST"])
def oracle_query_ajax(request):
    """AJAX endpoint for executing Oracle queries."""
    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        
        if not query:
            return JsonResponse({'error': 'Query is required'}, status=400)
        
        # Only allow SELECT queries for security
        if not query.upper().startswith('SELECT'):
            return JsonResponse({'error': 'Only SELECT queries are allowed'}, status=400)
        
        results = execute_oracle_query(query)
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results)
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def clear_sessions_view(request):
    """Debug view to clear all sessions"""
    from django.contrib.sessions.models import Session
    Session.objects.all().delete()
    
    # Also clear current session
    if hasattr(request, 'session'):
        request.session.flush()
    
    return HttpResponse("All sessions cleared. <a href='/app2/login/'>Go to login</a>") 