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
from .oracle_utils import (
    execute_oracle_query, test_oracle_connection, get_oracle_tables, get_oracle_table_info, 
    create_oracle_user, create_vendor, update_user_vendor_id, get_vendor_by_id,
    get_oracle_announcements, get_oracle_latest_news, get_oracle_announcement_count, get_oracle_news_count,
    get_oracle_user_messages, get_oracle_user_message_count,
    get_oracle_notifications, get_oracle_notification_count,
    get_oracle_open_tenders, get_oracle_tender_by_id, get_oracle_open_tenders_count,
    create_tender_application, get_vendor_tender_applications, check_tender_application_exists,
    get_tender_application_by_id, update_tender_application_status
)
# from shared_models.models import Tender, TenderApplication  # Commented out to remove dependency
from django.utils import timezone
from django.views.decorators.http import require_http_methods
import json
import logging

logger = logging.getLogger(__name__)

def home(request):
    #if not request.user.is_authenticated:
    #    return redirect('app2:login')
    
    # Check if user is Oracle user to get appropriate group_id
    user_group_id = None
    if request.user.is_authenticated and isinstance(request.user, OracleUser):
        user_group_id = getattr(request.user, 'group_id', None)
    
    # Get the latest announcements and news from Oracle database
    try:
        oracle_announcements = get_oracle_announcements(group_id=user_group_id, limit=5)
        oracle_latest_news = get_oracle_latest_news(group_id=user_group_id, limit=5)
        
        # Convert Oracle data to template-friendly format (similar to Django models)
        announcements = []
        for ann in oracle_announcements:
            announcements.append({
                'id': ann.get('ANNOUNCEMENT_ID'),
                'title': ann.get('TITLE'),
                'content': ann.get('CONTENT'),
                'created_at': ann.get('CREATED_AT'),
                'updated_at': ann.get('UPDATED_AT'),
                'is_active': ann.get('IS_ACTIVE'),
            })
        
        latest_news = []
        for news in oracle_latest_news:
            latest_news.append({
                'id': news.get('NEWS_ID'),
                'title': news.get('TITLE'),
                'content': news.get('CONTENT'),
                'image': {'url': news.get('IMAGE_URL')} if news.get('IMAGE_URL') else None,
                'created_at': news.get('CREATED_AT'),
                'updated_at': news.get('UPDATED_AT'),
                'is_active': news.get('IS_ACTIVE'),
            })
            
    except Exception as e:
        # Fallback to empty lists if Oracle query fails
        print(f"Error retrieving Oracle data: {str(e)}")
        announcements = []
        latest_news = []
        # Optional: Add error message
        if request.user.is_authenticated:
            messages.warning(request, 'خطا در بارگذاری اطلاعات. لطفاً دوباره تلاش کنید.')
    
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
    """View for displaying detailed information about a specific tender"""
    try:
        # Get tender details from Oracle
        tender = get_oracle_tender_by_id(tender_id)
        
        if not tender:
            messages.error(request, 'مناقصه مورد نظر یافت نشد.')
            return redirect('app2:tender_applications')
        
        # Check if user has already applied (for Oracle users)
        has_applied = False
        user_vendor_id = None
        
        if isinstance(request.user, OracleUser):
            user_company = getattr(request.user, 'company', None)
            if user_company and hasattr(user_company, 'vendor_id'):
                user_vendor_id = user_company.vendor_id
                if user_vendor_id:
                    has_applied = check_tender_application_exists(tender_id, user_vendor_id)
        
        # Format tender for template
        formatted_tender = {
            'id': tender.get('TENDER_ID'),
            'title': tender.get('TENDER_TITLE'),
            'description': tender.get('TENDER_DESCRIPTION'),
            'category_id': tender.get('CATEGORY_ID'),
            'start_date': tender.get('START_DATE'),
            'end_date': tender.get('END_DATE'),
            'submission_deadline': tender.get('SUBMISSION_DEADLINE'),
            'budget_amount': tender.get('BUDGET_AMOUNT'),
            'currency': tender.get('CURRENCY', 'ریال'),
            'status': tender.get('STATUS'),
            'created_date': tender.get('CREATED_DATE'),
        }
        
        context = {
            'tender': formatted_tender,
            'page_title': f'جزئیات مناقصه: {formatted_tender["title"]}',
            'has_applied': has_applied,
            'user_vendor_id': user_vendor_id
        }
        
        return render(request, 'app2/tender_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in tender_detail view: {str(e)}")
        messages.error(request, 'خطا در بارگذاری جزئیات مناقصه')
        return redirect('app2:tender_applications')

@login_required
def apply_to_tender(request, tender_id):
    """View for submitting a tender application"""
    try:
        # Check if user is Oracle user and has vendor
        if not isinstance(request.user, OracleUser):
            messages.error(request, 'فقط کاربران ثبت‌شده می‌توانند در مناقصات شرکت کنند.')
            return redirect('app2:tender_detail', tender_id=tender_id)
        
        user_company = getattr(request.user, 'company', None)
        if not user_company or not hasattr(user_company, 'vendor_id') or not user_company.vendor_id:
            messages.error(request, 'برای شرکت در مناقصه ابتدا باید اطلاعات شرکت خود را تکمیل کنید.')
            return redirect('app2:settings')
        
        vendor_id = user_company.vendor_id
        
        # Get tender details
        tender = get_oracle_tender_by_id(tender_id)
        if not tender:
            messages.error(request, 'مناقصه مورد نظر یافت نشد.')
            return redirect('app2:tender_applications')
        
        # Check if tender is still open
        if tender.get('STATUS', '').upper() != 'OPEN':
            messages.error(request, 'این مناقصه دیگر باز نیست.')
            return redirect('app2:tender_detail', tender_id=tender_id)
        
        # Check if already applied
        if check_tender_application_exists(tender_id, vendor_id):
            messages.warning(request, 'شما قبلاً برای این مناقصه درخواست ارسال کرده‌اید.')
            return redirect('app2:tender_detail', tender_id=tender_id)
        
        if request.method == 'POST':
            submission_notes = request.POST.get('submission_notes', '').strip()
            
            # Create the application
            application = create_tender_application(tender_id, vendor_id, submission_notes)
            
            if application:
                messages.success(request, 'درخواست شما با موفقیت ارسال شد!')
                return redirect('app2:my_applications')
            else:
                messages.error(request, 'خطا در ارسال درخواست. لطفاً دوباره تلاش کنید.')
        
        # Format tender for template
        formatted_tender = {
            'id': tender.get('TENDER_ID'),
            'title': tender.get('TENDER_TITLE'),
            'description': tender.get('TENDER_DESCRIPTION'),
            'submission_deadline': tender.get('SUBMISSION_DEADLINE'),
            'budget_amount': tender.get('BUDGET_AMOUNT'),
            'currency': tender.get('CURRENCY', 'ریال'),
        }
        
        context = {
            'tender': formatted_tender,
            'page_title': f'درخواست شرکت در مناقصه: {formatted_tender["title"]}'
        }
        
        return render(request, 'app2/apply_to_tender.html', context)
        
    except Exception as e:
        logger.error(f"Error in apply_to_tender view: {str(e)}")
        messages.error(request, 'خطا در پردازش درخواست')
        return redirect('app2:tender_detail', tender_id=tender_id)

@login_required
def my_applications(request):
    """View for displaying user's tender applications"""
    try:
        # Check if user is Oracle user and has vendor
        if not isinstance(request.user, OracleUser):
            messages.error(request, 'شما دسترسی به این بخش ندارید.')
            return redirect('app2:home')
        
        user_company = getattr(request.user, 'company', None)
        if not user_company or not hasattr(user_company, 'vendor_id') or not user_company.vendor_id:
            messages.info(request, 'برای مشاهده درخواست‌ها ابتدا باید اطلاعات شرکت خود را تکمیل کنید.')
            return redirect('app2:settings')
        
        vendor_id = user_company.vendor_id
        
        # Get vendor's applications
        applications = get_vendor_tender_applications(vendor_id, limit=50)
        
        # Format applications for template
        formatted_applications = []
        for app in applications:
            formatted_app = {
                'id': app.get('APPLICATION_ID'),
                'tender_id': app.get('TENDER_ID'),
                'tender_title': app.get('TENDER_TITLE'),
                'tender_description': app.get('TENDER_DESCRIPTION'),
                'submission_date': app.get('SUBMISSION_DATE'),
                'application_status': app.get('APPLICATION_STATUS'),
                'submission_notes': app.get('SUBMISSION_NOTES'),
                'budget_amount': app.get('BUDGET_AMOUNT'),
                'currency': app.get('CURRENCY', 'ریال'),
                'tender_status': app.get('TENDER_STATUS'),
                'submission_deadline': app.get('SUBMISSION_DEADLINE'),
            }
            formatted_applications.append(formatted_app)
        
        context = {
            'applications': formatted_applications,
            'total_count': len(formatted_applications),
            'page_title': 'درخواست‌های من'
        }
        
        return render(request, 'app2/my_applications.html', context)
        
    except Exception as e:
        logger.error(f"Error in my_applications view: {str(e)}")
        messages.error(request, 'خطا در بارگذاری درخواست‌ها')
        return redirect('app2:home')

@login_required
def application_detail(request, application_id):
    """Display detailed information about a specific application"""
    try:
        # Get application details from Oracle
        application = get_tender_application_by_id(application_id)
        
        if not application:
            messages.error(request, 'درخواست مورد نظر یافت نشد.')
            return redirect('app2:my_applications')
        
        # Check if this application belongs to the current user
        # (This would need proper vendor/user relationship checking)
        
        context = {
            'page_title': f'جزئیات درخواست #{application_id}',
            'application': application,
        }
        
        return render(request, 'app2/application_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error retrieving application details: {str(e)}")
        messages.error(request, 'خطا در بارگذاری جزئیات درخواست.')
        return redirect('app2:my_applications')

def news_announcements(request):
    # Check if user is Oracle user to get appropriate group_id
    user_group_id = None
    if request.user.is_authenticated and isinstance(request.user, OracleUser):
        user_group_id = getattr(request.user, 'group_id', None)
    
    # Get all announcements and news from Oracle database
    try:
        oracle_announcements = get_oracle_announcements(group_id=user_group_id, limit=50)  # Get more for full page
        oracle_latest_news = get_oracle_latest_news(group_id=user_group_id, limit=50)
        
        # Convert Oracle data to template-friendly format (similar to Django models)
        announcements = []
        for ann in oracle_announcements:
            announcements.append({
                'id': ann.get('ANNOUNCEMENT_ID'),
                'title': ann.get('TITLE'),
                'content': ann.get('CONTENT'),
                'created_at': ann.get('CREATED_AT'),
                'updated_at': ann.get('UPDATED_AT'),
                'is_active': ann.get('IS_ACTIVE'),
            })
        
        latest_news = []
        for news in oracle_latest_news:
            latest_news.append({
                'id': news.get('NEWS_ID'),
                'title': news.get('TITLE'),
                'content': news.get('CONTENT'),
                'image': {'url': news.get('IMAGE_URL')} if news.get('IMAGE_URL') else None,
                'created_at': news.get('CREATED_AT'),
                'updated_at': news.get('UPDATED_AT'),
                'is_active': news.get('IS_ACTIVE'),
            })
            
    except Exception as e:
        # Fallback to empty lists if Oracle query fails
        print(f"Error retrieving Oracle data for news_announcements: {str(e)}")
        announcements = []
        latest_news = []
        # Optional: Add error message
        if request.user.is_authenticated:
            messages.warning(request, 'خطا در بارگذاری اطلاعات. لطفاً دوباره تلاش کنید.')
    
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

def tender_applications(request):
    """View for displaying open tender applications"""
    try:
        # Get user's group_id if they're an Oracle user
        user_group_id = None
        oracle_user = getattr(request.user, 'oracle_user', None)
        if oracle_user and isinstance(oracle_user, dict):
            user_group_id = oracle_user.get('GROUP_ID')
        
        # Get open tenders from Oracle
        open_tenders = get_oracle_open_tenders(limit=50)
        
        # Format tenders for template
        formatted_tenders = []
        for tender in open_tenders:
            formatted_tender = {
                'id': tender.get('TENDER_ID'),
                'title': tender.get('TENDER_TITLE'),
                'description': tender.get('TENDER_DESCRIPTION'),
                'category_id': tender.get('CATEGORY_ID'),
                'start_date': tender.get('START_DATE'),
                'end_date': tender.get('END_DATE'),
                'submission_deadline': tender.get('SUBMISSION_DEADLINE'),
                'budget_amount': tender.get('BUDGET_AMOUNT'),
                'currency': tender.get('CURRENCY', 'ریال'),
                'status': tender.get('STATUS'),
                'created_date': tender.get('CREATED_DATE'),
            }
            formatted_tenders.append(formatted_tender)
        
        # Get count of open tenders
        open_tenders_count = get_oracle_open_tenders_count()
        
        context = {
            'tenders': formatted_tenders,
            'total_count': open_tenders_count,
            'page_title': 'مناقصات باز'
        }
        
        return render(request, 'app2/tender_applications.html', context)
        
    except Exception as e:
        logger.error(f"Error in tender_applications view: {str(e)}")
        # Fallback to empty list if Oracle fails
        context = {
            'tenders': [],
            'total_count': 0,
            'page_title': 'مناقصات باز',
            'error_message': 'خطا در بارگذاری اطلاعات مناقصات'
        }
        return render(request, 'app2/tender_applications.html', context) 