from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import App1User, Role, UserRole
from .forms import App1UserCreationForm, App1AuthenticationForm
from .auth_backend import App1AuthBackend
from django.contrib.auth.decorators import login_required, permission_required
from app2.models import Company, CompanyDocument, Notification, App2User
from django.contrib.auth.models import Permission
from django.db.models import Q
from django.utils import timezone
from shared_models.models import TenderApplication, Tender
from django.core.files.storage import FileSystemStorage
import os
from app1.models import TenderApplicationProcess
from app1.flows import TenderApplicationFlow
from django.db import models
from viewflow.workflow.models import Task
from django.http import JsonResponse
from django.db import transaction

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
    # Get all applications with related workflow information
    applications = TenderApplication.objects.select_related(
        'applicant',
        'applicant__user',
        'tender'
    ).prefetch_related(
        'applicant__documents'
    ).all().order_by('-submitted_at')

    # Get workflow processes and tasks for each application
    for application in applications:
        try:
            # Use filter().first() instead of get() to handle multiple processes
            process = TenderApplicationProcess.objects.filter(
                application=application
            ).order_by('-id').first()  # Get the most recent process
            
            if process:
                application.process = process
                
                # Get current task
                current_task = Task.objects.filter(
                    process=process,
                    status__in=['NEW', 'ASSIGNED', 'STARTED']
                ).select_related('owner').first()
                
                if current_task:
                    application.current_task = current_task
                    application.current_step = current_task.flow_task.name
                    application.assigned_to = current_task.owner
                else:
                    # Check if there are any completed tasks
                    last_task = Task.objects.filter(
                        process=process,
                        status='DONE'
                    ).select_related('owner').order_by('-finished').first()
                    
                    if last_task:
                        application.current_step = "تکمیل شده"
                        application.assigned_to = last_task.owner
                    else:
                        application.current_step = "در انتظار شروع"
                        application.assigned_to = None

                # Add workflow graph URL - using the correct URL pattern
                application.workflow_graph_url = f"/vf/tender_application/tenderapplication/{process.id}/chart/"
            else:
                # No process found
                application.process = None
                application.current_step = "در انتظار شروع"
                application.assigned_to = None
                application.current_task = None
                application.workflow_graph_url = None
                
        except Exception as e:
            print(f"Error processing application {application.id}: {str(e)}")
            application.process = None
            application.current_step = "خطا در پردازش"
            application.assigned_to = None
            application.current_task = None
            application.workflow_graph_url = None

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
        ).first()
        
        if existing_process:
            # Get the task - either unassigned or assigned to the current user
            task = Task.objects.filter(
                process=existing_process,
                status__in=['NEW', 'ASSIGNED']
            ).filter(
                models.Q(owner=None) | models.Q(owner=request.user)
            ).first()
            
            if task:
                # If the task is not assigned to the current user, assign it
                if task.status == 'NEW' or task.owner != request.user:
                    task.owner = request.user
                    task.status = 'ASSIGNED'
                    task.save()
                    messages.success(request, "Task assigned to you successfully.")
                else:
                    messages.info(request, "Task is already assigned to you.")
            else:
                messages.warning(request, "No pending task found in the workflow.")
        else:
            # Start the workflow
            process = TenderApplicationFlow.start_noninteractive.run(application_id=application.id)
            
            # Get the first task and assign it to the current user
            task = Task.objects.filter(
                process=process,
                status='NEW'
            ).first()
            
            if task:
                task.owner = request.user
                task.status = 'ASSIGNED'
                task.save()
                messages.success(request, "Workflow started and task assigned to you successfully.")
            else:
                messages.warning(request, "Workflow started but no task was created.")
        
        return redirect('app1:tender_applications')
    
    except TenderApplication.DoesNotExist:
        messages.error(request, "Application not found.")
        return redirect('app1:tender_applications')

@login_required
def tender_list(request):
    tenders = Tender.objects.all().order_by('-published_date')
    context = {
        'tenders': tenders,
    }
    return render(request, 'app1/tender/tender_list.html', context)

@login_required
@permission_required('app2.view_notification', raise_exception=True)
def notification_list(request):
    notifications = Notification.objects.all().order_by('-created_at')
    return render(request, 'app1/controls/notification_list.html', {'notifications': notifications})

@login_required
@permission_required('app2.add_notification', raise_exception=True)
def notification_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        message = request.POST.get('message')
        notification_type = request.POST.get('notification_type')
        
        Notification.objects.create(
            title=title,
            message=message,
            notification_type=notification_type
        )
        messages.success(request, 'نوتیفیکیشن با موفقیت ایجاد شد.')
        return redirect('app1:notification_list')
    
    return render(request, 'app1/controls/notification_create.html')

@login_required
@permission_required('app2.change_notification', raise_exception=True)
def notification_toggle(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.is_active = not notification.is_active
    notification.save()
    
    status = 'فعال' if notification.is_active else 'غیرفعال'
    messages.success(request, f'وضعیت نوتیفیکیشن به {status} تغییر یافت.')
    return redirect('app1:notification_list')

@login_required
@permission_required('app2.delete_notification', raise_exception=True)
def notification_delete(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id)
    notification.delete()
    messages.success(request, 'نوتیفیکیشن با موفقیت حذف شد.')
    return redirect('app1:notification_list')

@login_required
@permission_required('app2.view_app2user', raise_exception=True)
def participant_management(request):
    # Get all companies with their users and tender application counts
    companies = Company.objects.select_related('user').all()
    
    # Annotate each company with their tender application count
    for company in companies:
        company.tender_count = TenderApplication.objects.filter(applicant=company).count()
    
    context = {
        'companies': companies,
    }
    return render(request, 'app1/controls/participant_management.html', context)

@login_required
@permission_required('app2.view_company', raise_exception=True)
def company_details(request, company_id):
    company = get_object_or_404(Company, id=company_id)
    context = {
        'company': company,
        'documents': company.documents.all(),
        'tender_count': TenderApplication.objects.filter(applicant=company).count(),
    }
    return render(request, 'app1/controls/company_details.html', context)

@login_required
def initial_review(request, application_id):
    print("\n=== Initial Review Debug ===")
    application = get_object_or_404(TenderApplication, id=application_id)
    print(f"Application ID: {application.id}, Status: {application.status}")
    
    process = TenderApplicationProcess.objects.filter(application=application).first()
    print(f"Process found: {process is not None}")
    
    if not process:
        messages.error(request, 'No workflow process found for this application.')
        return redirect('app1:tender_applications')
    
    # Get the current task - check for all active statuses
    current_task = Task.objects.filter(
        process=process,
        status__in=['NEW', 'ASSIGNED', 'STARTED']
    ).first()
    
    print(f"Current task found: {current_task is not None}")
    if current_task:
        print(f"Task status: {current_task.status}")
        print(f"Task flow_task: {current_task.flow_task}")
        print(f"Task flow_task name: {current_task.flow_task.name}")
    
    if not current_task or current_task.flow_task.name != 'review':
        messages.error(request, 'This application is not in the initial review stage.')
        return redirect('app1:tender_applications')
    
    if request.method == 'POST':
        print("\nProcessing POST request...")
        process.notes = request.POST.get('notes', '')
        process.is_shortlisted = request.POST.get('is_shortlisted') == 'on'
        process.is_rejected = request.POST.get('is_rejected') == 'on'
        process.save()
        print(f"Process updated - is_shortlisted: {process.is_shortlisted}, is_rejected: {process.is_rejected}")
        
        # Update application status based on the initial review decision
        if process.is_rejected:
            application.status = 'rejected'
        elif process.is_shortlisted:
            application.status = 'shortlisted'
        else:
            application.status = 'reviewed'
        application.save()
        print(f"Application status updated to: {application.status}")
        
        # Complete the task and activate the next task in the workflow
        with transaction.atomic():
            print("\nCompleting task using activation...")
            
            # Create a flow instance and import necessary classes
            from viewflow.workflow.activation import Activation
            from viewflow.workflow.flow import Flow, Function
            
            # Set the task as done
            current_task.status = 'DONE'
            current_task.finished = timezone.now()
            current_task.owner = request.user  # Ensure the task has an owner
            current_task.save()
            print(f"Task marked as DONE at {current_task.finished}")
            
            # Now we need to advance the workflow by creating the next task
            flow = TenderApplicationFlow()
            
            # Get the next node to process based on the flow definition
            if process.is_shortlisted:
                print("Activating path for shortlisted application...")
                # Create a detailed_review task 
                next_task = Task.objects.create(
                    process=process,
                    flow_task=flow.detailed_review,
                    status='NEW',
                    created=timezone.now()
                )
                # Set the previous task properly
                next_task.previous.set([current_task])
                print(f"Created next task: {next_task.flow_task.name}")
            elif process.is_rejected:
                print("Activating path for rejected application...")
                # Create a notify_rejection task
                next_task = Task.objects.create(
                    process=process,
                    flow_task=flow.notify_rejection,
                    status='NEW', 
                    created=timezone.now()
                )
                # Set the previous task properly
                next_task.previous.set([current_task])
                print(f"Created next task: {next_task.flow_task.name}")
                
                # If it's a function node, execute it immediately
                if isinstance(next_task.flow_task, Function):
                    print(f"Flow task type: {type(next_task.flow_task)}")
                    try:
                        # Get the activation and execute the function
                        activation = next_task.flow_task.activation_class(next_task)
                        activation.prepare()
                        activation.execute()
                        activation.done()
                        next_task.status = 'DONE'
                        next_task.finished = timezone.now()
                        next_task.save()
                        print("Function task executed automatically")
                        
                        # Create the end task after function completes
                        end_task = Task.objects.create(
                            process=process,
                            flow_task=flow.end,
                            status='DONE',
                            created=timezone.now(),
                            started=timezone.now(),
                            finished=timezone.now()
                        )
                        end_task.previous.set([next_task])
                        print("Created end task after function execution")
                    except Exception as e:
                        print(f"Error executing function: {str(e)}")
            else:
                print("Activating path to end the flow...")
                # Create an end task 
                next_task = Task.objects.create(
                    process=process,
                    flow_task=flow.end,
                    status='DONE',
                    created=timezone.now(),
                    started=timezone.now(),
                    finished=timezone.now()
                )
                # Set the previous task properly
                next_task.previous.set([current_task])
                print(f"Created end task: {next_task.flow_task.name}")
        
        messages.success(request, 'Initial review completed successfully.')
        return redirect('app1:tender_applications')
    
    return render(request, 'app1/tender/initial_review.html', {
        'application': application,
        'process': process,
        'form': {
            'notes': {'value': process.notes},
            'is_shortlisted': {'value': process.is_shortlisted},
            'is_rejected': {'value': process.is_rejected}
        }
    })

@login_required
def detailed_review(request, application_id):
    print("\n=== Detailed Review Debug ===")
    application = get_object_or_404(TenderApplication, id=application_id)
    print(f"Application ID: {application.id}, Status: {application.status}")
    
    process = TenderApplicationProcess.objects.filter(application=application).first()
    print(f"Process found: {process is not None}")
    
    if not process:
        messages.error(request, 'No workflow process found for this application.')
        return redirect('app1:tender_applications')
    
    # Get the current task - check for all active statuses
    current_task = Task.objects.filter(
        process=process,
        status__in=['NEW', 'ASSIGNED', 'STARTED']
    ).first()
    
    print(f"Current task found: {current_task is not None}")
    if current_task:
        print(f"Task status: {current_task.status}")
        print(f"Task flow_task: {current_task.flow_task}")
        print(f"Task flow_task name: {current_task.flow_task.name}")
    
    if not current_task or current_task.flow_task.name != 'detailed_review':
        messages.error(request, 'This application is not in the detailed review stage.')
        return redirect('app1:tender_applications')
    
    if request.method == 'POST':
        print("\nProcessing POST request...")
        process.notes = request.POST.get('notes', '')
        process.is_accepted = request.POST.get('is_accepted') == 'on'
        process.is_rejected = request.POST.get('is_rejected') == 'on'
        process.save()
        print(f"Process updated - is_accepted: {process.is_accepted}, is_rejected: {process.is_rejected}")
        
        # Update application status based on the detailed review decision
        if process.is_rejected:
            application.status = 'rejected'
        elif process.is_accepted:
            application.status = 'accepted'
        else:
            application.status = 'reviewed'
        application.save()
        print(f"Application status updated to: {application.status}")
        
        # Complete the task and activate the next task in the workflow
        with transaction.atomic():
            print("\nCompleting task using activation...")
            
            # Create a flow instance and import necessary classes
            from viewflow.workflow.activation import Activation
            from viewflow.workflow.flow import Flow, Function
            
            # Set the task as done
            current_task.status = 'DONE'
            current_task.finished = timezone.now()
            current_task.owner = request.user  # Ensure the task has an owner
            current_task.save()
            print(f"Task marked as DONE at {current_task.finished}")
            
            # Now we need to advance the workflow by creating the next task
            flow = TenderApplicationFlow()
            
            # Get the next node to process based on the flow definition
            if process.is_accepted:
                print("Activating path for accepted application...")
                # Create a notify_acceptance task
                next_task = Task.objects.create(
                    process=process,
                    flow_task=flow.notify_acceptance,
                    status='NEW',
                    created=timezone.now()
                )
                # Set the previous task properly
                next_task.previous.set([current_task])
                print(f"Created next task: {next_task.flow_task.name}")
                
                # If it's a function node, execute it immediately
                if isinstance(next_task.flow_task, Function):
                    print(f"Flow task type: {type(next_task.flow_task)}")
                    try:
                        # Get the activation and execute the function
                        activation = next_task.flow_task.activation_class(next_task)
                        activation.prepare()
                        activation.execute()
                        activation.done()
                        next_task.status = 'DONE'
                        next_task.finished = timezone.now()
                        next_task.save()
                        print("Function task executed automatically")
                        
                        # Create the end task after function completes
                        end_task = Task.objects.create(
                            process=process,
                            flow_task=flow.end,
                            status='DONE',
                            created=timezone.now(),
                            started=timezone.now(),
                            finished=timezone.now()
                        )
                        end_task.previous.set([next_task])
                        print("Created end task after function execution")
                    except Exception as e:
                        print(f"Error executing function: {str(e)}")
            elif process.is_rejected:
                print("Activating path for rejected application...")
                # Create a notify_rejection task
                next_task = Task.objects.create(
                    process=process,
                    flow_task=flow.notify_rejection,
                    status='NEW',
                    created=timezone.now()
                )
                # Set the previous task properly
                next_task.previous.set([current_task])
                print(f"Created next task: {next_task.flow_task.name}")
                
                # If it's a function node, execute it immediately
                if isinstance(next_task.flow_task, Function):
                    print(f"Flow task type: {type(next_task.flow_task)}")
                    try:
                        # Get the activation and execute the function
                        activation = next_task.flow_task.activation_class(next_task)
                        activation.prepare()
                        activation.execute()
                        activation.done()
                        next_task.status = 'DONE'
                        next_task.finished = timezone.now()
                        next_task.save()
                        print("Function task executed automatically")
                        
                        # Create the end task after function completes
                        end_task = Task.objects.create(
                            process=process,
                            flow_task=flow.end,
                            status='DONE',
                            created=timezone.now(),
                            started=timezone.now(),
                            finished=timezone.now()
                        )
                        end_task.previous.set([next_task])
                        print("Created end task after function execution")
                    except Exception as e:
                        print(f"Error executing function: {str(e)}")
            else:
                print("Activating path to end the flow...")
                # Create an end task
                next_task = Task.objects.create(
                    process=process,
                    flow_task=flow.end,
                    status='DONE',
                    created=timezone.now(),
                    started=timezone.now(),
                    finished=timezone.now()
                )
                # Set the previous task properly
                next_task.previous.set([current_task])
                print(f"Created end task: {next_task.flow_task.name}")
        
        messages.success(request, 'Detailed review completed successfully.')
        return redirect('app1:tender_applications')
    
    return render(request, 'app1/tender/detailed_review.html', {
        'application': application,
        'process': process,
        'form': {
            'notes': {'value': process.notes},
            'is_accepted': {'value': process.is_accepted},
            'is_rejected': {'value': process.is_rejected}
        }
    }) 
       