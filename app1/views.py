from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .models import App1User, Role, UserRole, FlowTemplate, FlowStep, TenderApplicationProcess
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
from app1.flows import TenderApplicationFlow
from django.db import models
from viewflow.workflow.models import Task
from viewflow.workflow.flow import Function
from django.http import JsonResponse
from django.db import transaction
import re

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
                
                # If it's a function node, execute it directly
                if isinstance(next_task.flow_task, Function):
                    print(f"Flow task type: {type(next_task.flow_task)}")
                    try:
                        # Execute the function directly
                        print("Executing rejection notification function directly...")
                        flow.send_rejection_notification(next_task.flow_task.activation_class(next_task))
                        
                        # Mark the task as done
                        next_task.status = 'DONE'
                        next_task.finished = timezone.now()
                        next_task.save()
                        print("Function task completed successfully")
                        
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
                        print(f"Error executing rejection function: {str(e)}")
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
                
                # If it's a function node, execute it directly
                if isinstance(next_task.flow_task, Function):
                    print(f"Flow task type: {type(next_task.flow_task)}")
                    try:
                        # Execute the function directly
                        print("Executing acceptance notification function directly...")
                        flow.send_acceptance_notification(next_task.flow_task.activation_class(next_task))
                        
                        # Mark the task as done
                        next_task.status = 'DONE'
                        next_task.finished = timezone.now()
                        next_task.save()
                        print("Function task completed successfully")
                        
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
                        print(f"Error executing acceptance function: {str(e)}")
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
                
                # If it's a function node, execute it directly
                if isinstance(next_task.flow_task, Function):
                    print(f"Flow task type: {type(next_task.flow_task)}")
                    try:
                        # Execute the function directly
                        print("Executing rejection notification function directly...")
                        flow.send_rejection_notification(next_task.flow_task.activation_class(next_task))
                        
                        # Mark the task as done
                        next_task.status = 'DONE'
                        next_task.finished = timezone.now()
                        next_task.save()
                        print("Function task completed successfully")
                        
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
                    except Exception as e:
                        print(f"Error executing rejection function: {str(e)}")
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

@login_required
@permission_required('app1.view_flow_template', raise_exception=True)
def flow_template_list(request):
    """View all flow templates"""
    templates = FlowTemplate.objects.all().order_by('-updated_at')
    return render(request, 'app1/flowdesigner/template_list.html', {'templates': templates})

@login_required
@permission_required('app1.create_flow_template', raise_exception=True)
def flow_template_create(request):
    """Create a new flow template"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        flow_type = request.POST.get('flow_type')
        app_name = request.POST.get('app_name')
        process_class = request.POST.get('process_class')
        
        template = FlowTemplate.objects.create(
            name=name,
            description=description,
            flow_type=flow_type,
            app_name=app_name,
            process_class=process_class,
            created_by=request.user
        )
        
        # Create default Start and End steps
        start_step = FlowStep.objects.create(
            flow_template=template,
            name='start',
            step_type='start',
            position=1,
            x_coord=100,
            y_coord=100
        )
        
        end_step = FlowStep.objects.create(
            flow_template=template,
            name='end',
            step_type='end',
            position=999,
            x_coord=500,
            y_coord=100
        )
        
        messages.success(request, 'قالب جریان کار با موفقیت ایجاد شد.')
        return redirect('app1:flow_designer', template_id=template.id)
    
    return render(request, 'app1/flowdesigner/template_create.html')

@login_required
@permission_required('app1.view_flow_template', raise_exception=True)
def flow_designer(request, template_id):
    """Flow designer interface for a specific template"""
    template = get_object_or_404(FlowTemplate, id=template_id)
    steps = FlowStep.objects.filter(flow_template=template).order_by('position')
    
    # Get available view classes from ViewFlow
    view_classes = [
        'views.CreateProcessView',
        'views.UpdateProcessView',
        'views.DetailProcessView',
    ]
    
    # Get process model fields for selection
    process_fields = []
    try:
        from django.apps import apps
        model_path = template.process_class.split('.')
        if len(model_path) > 1:
            app_label, model_name = model_path[0], model_path[-1]
            model = apps.get_model(app_label, model_name)
            for field in model._meta.get_fields():
                if hasattr(field, 'name') and not field.name.startswith('_'):
                    process_fields.append(field.name)
        else:
            # Try to find any local model matching the name
            for model in apps.get_models():
                if model.__name__ == template.process_class:
                    for field in model._meta.get_fields():
                        if hasattr(field, 'name') and not field.name.startswith('_'):
                            process_fields.append(field.name)
    except Exception as e:
        messages.warning(request, f'Unable to load process fields: {str(e)}')
    
    context = {
        'template': template,
        'steps': steps,
        'view_classes': view_classes,
        'process_fields': process_fields,
    }
    
    return render(request, 'app1/flowdesigner/flow_designer.html', context)

@login_required
@permission_required('app1.edit_flow_template', raise_exception=True)
def flow_step_create(request, template_id):
    """Create a new step in the flow template"""
    template = get_object_or_404(FlowTemplate, id=template_id)
    
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name')
        step_type = request.POST.get('step_type')
        
        # Convert coordinates to integers with default values
        try:
            x_coord = int(request.POST.get('x_coord', 200))
        except (ValueError, TypeError):
            x_coord = 200
            
        try:
            y_coord = int(request.POST.get('y_coord', 200))
        except (ValueError, TypeError):
            y_coord = 200
        
        # Validate required fields
        if not name or not step_type:
            return JsonResponse({'success': False, 'error': 'Name and step type are required'})
        
        # Get the maximum position and add 1
        max_position = FlowStep.objects.filter(flow_template=template).aggregate(models.Max('position'))['position__max'] or 0
        
        # Create the step
        try:
            step = FlowStep.objects.create(
                flow_template=template,
                name=name,
                step_type=step_type,
                position=max_position + 1,
                x_coord=x_coord,
                y_coord=y_coord
            )
            
            # Additional fields based on step type
            if step_type == 'view':
                step.view_class = request.POST.get('view_class')
                step.view_fields = request.POST.get('view_fields')
                step.auto_create_permission = request.POST.get('auto_create_permission') == 'on'
                step.save()
            
            elif step_type == 'function':
                step.function_name = request.POST.get('function_name')
                step.save()
            
            elif step_type == 'if':
                step.condition_type = request.POST.get('condition_type')
                if step.condition_type == 'field_check':
                    step.condition_field = request.POST.get('condition_field')
                    step.condition_value = request.POST.get('condition_value')
                else:
                    step.condition_code = request.POST.get('condition_code')
                step.save()
            
            return JsonResponse({'success': True, 'step_id': step.id})
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@permission_required('app1.edit_flow_template', raise_exception=True)
def flow_step_update(request, step_id):
    """Update a flow step"""
    step = get_object_or_404(FlowStep, id=step_id)
    
    if request.method == 'POST':
        # Update basic info
        step.name = request.POST.get('name', step.name)
        
        # Update position
        if 'x_coord' in request.POST and 'y_coord' in request.POST:
            step.x_coord = request.POST.get('x_coord')
            step.y_coord = request.POST.get('y_coord')
        
        # Update specific fields based on step type
        if step.step_type == 'view':
            step.view_class = request.POST.get('view_class', step.view_class)
            step.view_fields = request.POST.get('view_fields', step.view_fields)
            step.auto_create_permission = request.POST.get('auto_create_permission') == 'on'
        
        elif step.step_type == 'function':
            step.function_name = request.POST.get('function_name', step.function_name)
        
        elif step.step_type == 'if':
            step.condition_type = request.POST.get('condition_type', step.condition_type)
            if step.condition_type == 'field_check':
                step.condition_field = request.POST.get('condition_field', step.condition_field)
                step.condition_value = request.POST.get('condition_value', step.condition_value)
            else:
                step.condition_code = request.POST.get('condition_code', step.condition_code)
        
        step.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@permission_required('app1.edit_flow_template', raise_exception=True)
def flow_step_delete(request, step_id):
    """Delete a flow step"""
    step = get_object_or_404(FlowStep, id=step_id)
    
    # Prevent deleting the start or end steps
    if step.step_type in ['start', 'end']:
        return JsonResponse({'success': False, 'error': 'Cannot delete start or end steps'})
    
    # Delete the step
    step.delete()
    
    return JsonResponse({'success': True})

@login_required
@permission_required('app1.edit_flow_template', raise_exception=True)
def flow_connection_update(request):
    """Update connections between steps"""
    if request.method == 'POST':
        source_id = request.POST.get('source_id')
        target_id = request.POST.get('target_id')
        connection_type = request.POST.get('connection_type', 'next')
        
        source = get_object_or_404(FlowStep, id=source_id)
        target = get_object_or_404(FlowStep, id=target_id)
        
        # Prevent connecting to start or from end
        if target.step_type == 'start':
            return JsonResponse({'success': False, 'error': 'Cannot connect to start step'})
        
        if source.step_type == 'end':
            return JsonResponse({'success': False, 'error': 'Cannot connect from end step'})
        
        # Update the connection
        if connection_type == 'next' and source.step_type != 'if':
            source.next_step = target
            source.save()
        
        elif connection_type == 'true' and source.step_type == 'if':
            source.branch_true = target
            source.save()
        
        elif connection_type == 'false' and source.step_type == 'if':
            source.branch_false = target
            source.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
@permission_required('app1.generate_flow_code', raise_exception=True)
def generate_flow_code(request, template_id):
    """Generate and save the flow code"""
    template = get_object_or_404(FlowTemplate, id=template_id)
    steps = FlowStep.objects.filter(flow_template=template).order_by('position')
    
    # Find the start step
    start_step = steps.filter(step_type='start').first()
    if not start_step:
        messages.error(request, 'جریان کار باید یک مرحله شروع داشته باشد.')
        return redirect('app1:flow_designer', template_id=template.id)
    
    # Find the end step
    end_step = steps.filter(step_type='end').first()
    if not end_step:
        messages.error(request, 'جریان کار باید یک مرحله پایان داشته باشد.')
        return redirect('app1:flow_designer', template_id=template.id)
    
    # Generate the flow code
    flow_class_name = ''.join(word.capitalize() for word in template.name.split())
    if not flow_class_name.endswith('Flow'):
        flow_class_name += 'Flow'
    
    # Import statements
    imports = [
        'from viewflow import this',
        'from viewflow.workflow import flow, lock, act',
        'from viewflow.workflow.flow import views',
        'from django.utils import timezone',
        f'from .models import {template.process_class}',
    ]
    
    # Flow class definition
    flow_code = [
        f'class {flow_class_name}(flow.Flow):',
        f'    process_class = {template.process_class}',
        f'    app_name = "{template.app_name}"',
        '    ',
        f'    process_title = "{template.name}"',
        f'    process_description = "{template.description}"',
        '    ',
    ]
    
    # Process steps
    steps_code = []
    function_definitions = []
    
    # Process each step
    for step in steps:
        if step.step_type == 'start':
            next_step = step.next_step
            if next_step:
                steps_code.append(f'    start = flow.Start(this.start_process).Next(this.{next_step.name})')
            else:
                steps_code.append(f'    start = flow.Start(this.start_process).Next(this.end)')
            
            # Add the properly formatted start_process function definition that handles both activation and request
            function_definitions.append(
                '    def start_process(self, activation, **kwargs):\n'
                '        """Initialize the process.\n'
                '        \n'
                '        This method can accept either an activation object or request parameters.\n'
                '        """\n'
                '        # Initialize process data\n'
                '        activation.process.save()\n'
                '        return activation.process'
            )
        
        elif step.step_type == 'view':
            fields_str = step.view_fields if step.view_fields else ''
            fields_list = [f'"{field.strip()}"' for field in fields_str.split(',') if field.strip()]
            
            view_code = f'    {step.name} = (\n'
            view_code += f'        flow.View({step.view_class}.as_view(fields=[{", ".join(fields_list)}]))\n'
            view_code += f'        .Annotation(title="{step.name}")\n'
            
            if step.auto_create_permission:
                view_code += '        .Permission(auto_create=True)\n'
            
            if step.next_step:
                view_code += f'        .Next(this.{step.next_step.name})\n'
            else:
                view_code += '        .Next(this.end)\n'
            
            view_code += '    )'
            steps_code.append(view_code)
        
        elif step.step_type == 'function':
            function_code = f'    {step.name} = (\n'
            function_code += f'        flow.Function(this.{step.function_name})\n'
            
            if step.next_step:
                function_code += f'        .Next(this.{step.next_step.name})\n'
            else:
                function_code += '        .Next(this.end)\n'
            
            function_code += '    )'
            steps_code.append(function_code)
            
            # Add a placeholder function definition
            function_definitions.append(
                f'    def {step.function_name}(self, activation):\n'
                f'        # Function implementation for {step.name}\n'
                '        pass'
            )
        
        elif step.step_type == 'if':
            condition_code = ''
            if step.condition_type == 'field_check':
                condition_code = f'lambda activation: activation.process.{step.condition_field} == "{step.condition_value}"'
            else:
                # Use user-defined condition code
                condition_code = step.condition_code or 'lambda activation: False'
            
            if_code = f'    {step.name} = (\n'
            if_code += f'        flow.If({condition_code})\n'
            
            if step.branch_true:
                if_code += f'        .Then(this.{step.branch_true.name})\n'
            else:
                if_code += '        .Then(this.end)\n'
            
            if step.branch_false:
                if_code += f'        .Else(this.{step.branch_false.name})\n'
            else:
                if_code += '        .Else(this.end)\n'
            
            if_code += '    )'
            steps_code.append(if_code)
        
        elif step.step_type == 'end':
            steps_code.append('    end = flow.End()')
    
    # Combine all code sections
    all_code = '\n'.join(imports) + '\n\n\n' + '\n'.join(flow_code) + '\n\n' + '\n\n'.join(steps_code) + '\n\n\n' + '\n\n'.join(function_definitions)
    
    # Save the code to flows.py
    try:
        import os
        
        # Get the app path
        app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        flow_file_path = os.path.join(app_path, 'app1', 'flows.py')
        
        # Read the existing file
        with open(flow_file_path, 'r') as f:
            existing_code = f.read()
        
        # Check if the flow class already exists
        if f'class {flow_class_name}(flow.Flow):' in existing_code:
            # Update the existing class
            # This is a simple approach - in a real implementation, you might want to use AST or similar
            start_idx = existing_code.find(f'class {flow_class_name}(flow.Flow):')
            if start_idx >= 0:
                # Find the next class definition or EOF
                next_class_idx = existing_code.find('class ', start_idx + 1)
                if next_class_idx >= 0:
                    existing_code = existing_code[:start_idx] + all_code + '\n\n' + existing_code[next_class_idx:]
                else:
                    existing_code = existing_code[:start_idx] + all_code
        else:
            # Append the new class
            existing_code += '\n\n\n' + all_code
        
        # Write back to the file
        with open(flow_file_path, 'w') as f:
            f.write(existing_code)
        
        # Update the template
        template.code_generated = True
        template.save()
        
        # Update urls.py to include the new flow
        try:
            urls_file_path = os.path.join(app_path, 'config', 'urls.py')
            
            if os.path.exists(urls_file_path):
                with open(urls_file_path, 'r') as f:
                    urls_code = f.read()
                
                # Remove from imports
                import_pattern = re.compile(fr'from app1\.flows import (.*{flow_class_name}.*)')
                match = import_pattern.search(urls_code)
                if match:
                    imports = match.group(1)
                    # Remove just this class from the imports
                    if f', {flow_class_name},' in imports:
                        new_imports = imports.replace(f', {flow_class_name}', '')
                    elif f', {flow_class_name}' in imports:
                        new_imports = imports.replace(f', {flow_class_name}', '')
                    elif f'{flow_class_name}, ' in imports:
                        new_imports = imports.replace(f'{flow_class_name}, ', '')
                    else:
                        new_imports = imports.replace(f'{flow_class_name}', '')
                    
                    urls_code = import_pattern.sub(f'from app1.flows import {new_imports}', urls_code)
                    
                    # If we ended up with empty imports (e.g., "from app1.flows import "), remove the line
                    if 'from app1.flows import \n' in urls_code:
                        urls_code = urls_code.replace('from app1.flows import \n', '')
                
                # Find and remove the entire Application block if it only contains this flow
                app_pattern = fr"Application\(\s*title='[^']*',\s*icon='[^']*',\s*app_name='{template.app_name}',\s*viewsets=\[\s*FlowAppViewset\({flow_class_name},[^\]]*\]\s*\),\s*"
                urls_code = re.sub(app_pattern, '', urls_code)
                
                # If the Application contains other flows, just remove this one
                flow_pattern = fr"FlowAppViewset\({flow_class_name},[^\n]*\n"
                urls_code = re.sub(flow_pattern, '', urls_code)
                
                # Clean up any trailing commas in the Site viewsets list
                urls_code = urls_code.replace('],\n])', ']\n])')
                
                # Write back to the file
                with open(urls_file_path, 'w') as f:
                    f.write(urls_code)
            
            messages.success(request, 'کد جریان کار با موفقیت تولید و در urls.py ثبت شد.')
            
        except Exception as e:
            messages.warning(request, f'کد جریان کار تولید شد اما ثبت در urls.py با خطا مواجه شد: {str(e)}')
        
        return redirect('app1:flow_template_list')
        
    except Exception as e:
        messages.error(request, f'خطا در تولید کد جریان کار: {str(e)}')
        return redirect('app1:flow_designer', template_id=template.id)

@login_required
@permission_required('app1.delete_flow_template', raise_exception=True)
def flow_template_delete(request, template_id):
    """Delete a flow template and its code from flows.py and urls.py"""
    template = get_object_or_404(FlowTemplate, id=template_id)
    
    # Only proceed if this is a POST request (to prevent accidental deletion via GET)
    if request.method != 'POST':
        messages.error(request, 'برای حذف جریان کار باید فرم را ارسال کنید.')
        return redirect('app1:flow_template_list')
    
    # Generate the flow class name in the same way as when generating code
    flow_class_name = ''.join(word.capitalize() for word in template.name.split())
    if not flow_class_name.endswith('Flow'):
        flow_class_name += 'Flow'
    
    try:
        import os
        import re
        
        # Get the app path
        app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        flow_file_path = os.path.join(app_path, 'app1', 'flows.py')
        
        # 1. Remove from flows.py if the class exists
        if os.path.exists(flow_file_path):
            with open(flow_file_path, 'r') as f:
                existing_code = f.read()
            
            # Find the flow class definition
            start_idx = existing_code.find(f'class {flow_class_name}(flow.Flow):')
            if start_idx >= 0:
                # Find the next class definition or EOF
                next_class_idx = existing_code.find('class ', start_idx + 1)
                if next_class_idx >= 0:
                    # Remove this class and keep everything else
                    existing_code = existing_code[:start_idx] + existing_code[next_class_idx:]
                else:
                    # This is the last class, remove from start to the end
                    # First, find the last import line to keep the imports
                    last_import_idx = existing_code.rfind('import', 0, start_idx)
                    if last_import_idx >= 0:
                        end_import_line = existing_code.find('\n', last_import_idx)
                        if end_import_line >= 0:
                            existing_code = existing_code[:end_import_line + 2]  # Keep an extra blank line
            
                # Write back to the file
                with open(flow_file_path, 'w') as f:
                    f.write(existing_code)
        
        # 2. Remove from urls.py
        urls_file_path = os.path.join(app_path, 'config', 'urls.py')
        if os.path.exists(urls_file_path):
            with open(urls_file_path, 'r') as f:
                urls_code = f.read()
            
            # Remove from imports
            import_pattern = re.compile(fr'from app1\.flows import (.*{flow_class_name}.*)')
            match = import_pattern.search(urls_code)
            if match:
                imports = match.group(1)
                # Remove just this class from the imports
                if f', {flow_class_name},' in imports:
                    new_imports = imports.replace(f', {flow_class_name}', '')
                elif f', {flow_class_name}' in imports:
                    new_imports = imports.replace(f', {flow_class_name}', '')
                elif f'{flow_class_name}, ' in imports:
                    new_imports = imports.replace(f'{flow_class_name}, ', '')
                else:
                    new_imports = imports.replace(f'{flow_class_name}', '')
                
                urls_code = import_pattern.sub(f'from app1.flows import {new_imports}', urls_code)
                
                # If we ended up with empty imports (e.g., "from app1.flows import "), remove the line
                if 'from app1.flows import \n' in urls_code:
                    urls_code = urls_code.replace('from app1.flows import \n', '')
            
            # Handle Custom Flow Deletion - Check for empty Application blocks
            # Find any Application blocks that have empty viewsets
            empty_app_pattern = re.compile(r"Application\(\s*title='[^']*',\s*icon='[^']*',\s*app_name='[^']*',\s*viewsets=\[\s*\]\s*\),")
            urls_code = empty_app_pattern.sub('', urls_code)
            
            # Also find application blocks with our app_name but no registered viewsets (including with indentation and newlines)
            app_name_pattern = re.compile(fr"Application\(\s*title='[^']*',\s*icon='[^']*',\s*app_name='{template.app_name}',\s*viewsets=\[\s*\]\s*\),")
            urls_code = app_name_pattern.sub('', urls_code)
            
            # More complex pattern to match indented empty viewsets
            complex_pattern = re.compile(fr"Application\(\s*title='[^']*',\s*icon='[^']*',\s*app_name='{template.app_name}',\s*viewsets=\[\s*\n\s*\]\s*\),")
            urls_code = complex_pattern.sub('', urls_code)
            
            # Remove any FlowAppViewset entries for this flow
            flow_viewset_pattern = re.compile(fr"FlowAppViewset\({flow_class_name}[^\n]*\n")
            urls_code = flow_viewset_pattern.sub('', urls_code)
            
            # Clean up any trailing commas in the Site viewsets list
            urls_code = urls_code.replace('],\n])', ']\n])')
            
            # Write back to the file
            with open(urls_file_path, 'w') as f:
                f.write(urls_code)
        
        # 3. Delete all steps associated with this template
        FlowStep.objects.filter(flow_template=template).delete()
        
        # 4. Delete the template itself
        template_name = template.name
        template.delete()
        
        messages.success(request, f'جریان کار "{template_name}" با موفقیت حذف شد.')
        
    except Exception as e:
        messages.error(request, f'خطا در حذف جریان کار: {str(e)}')
    
    return redirect('app1:flow_template_list')

@login_required
def role_review(request, application_id, role):
    """Generic view for role-based reviews"""
    application = get_object_or_404(TenderApplication, id=application_id)
    process = TenderApplicationProcess.objects.filter(application=application).first()
    
    if not process:
        messages.error(request, 'No workflow process found for this application.')
        return redirect('app1:tender_applications')
    
    # Get the current task
    current_task = Task.objects.filter(
        process=process,
        status__in=['NEW', 'ASSIGNED', 'STARTED']
    ).first()
    
    if not current_task:
        messages.error(request, 'No active task found for this application.')
        return redirect('app1:tender_applications')
    
    # Get role display name from flow class
    flow = TenderApplicationFlow()
    role_display_names = flow.ROLE_DISPLAY_NAMES
    
    if role not in role_display_names:
        messages.error(request, 'Invalid role specified.')
        return redirect('app1:tender_applications')
    
    # Check if user has the required role
    if not request.user.has_role(role):
        messages.error(request, 'You do not have permission to perform this review.')
        return redirect('app1:tender_applications')
    
    if request.method == 'POST':
        # Prepare review data
        review_data = {
            'notes': request.POST.get('notes', ''),
            'is_accepted': request.POST.get('is_accepted') == 'on',
            'is_rejected': request.POST.get('is_rejected') == 'on'
        }
        
        try:
            # Handle the review process using flow function
            flow.handle_role_review(process, current_task, role, request.user, review_data)
            messages.success(request, f'Review completed successfully by {role_display_names[role]}.')
        except Exception as e:
            messages.error(request, f'Error processing review: {str(e)}')
        
        return redirect('app1:tender_applications')
    
    return render(request, 'app1/tender/role_review.html', {
        'application': application,
        'process': process,
        'role': role_display_names[role],
        'form': {
            'notes': {'value': process.notes},
            'is_accepted': {'value': process.is_accepted},
            'is_rejected': {'value': process.is_rejected}
        }
    })

# Role-specific view functions
def purchase_expert_review(request, application_id):
    return role_review(request, application_id, 'purchase_expert')

def team_leader_review(request, application_id):
    return role_review(request, application_id, 'team_leader')

def supply_chain_manager_review(request, application_id):
    return role_review(request, application_id, 'supply_chain_manager')

def technical_evaluator_review(request, application_id):
    return role_review(request, application_id, 'technical_evaluator')

def financial_deputy_review(request, application_id):
    return role_review(request, application_id, 'financial_deputy')

def financial_manager_review(request, application_id):
    return role_review(request, application_id, 'financial_manager')

def commercial_team_evaluator_review(request, application_id):
    return role_review(request, application_id, 'commercial_team_evaluator')

def financial_team_evaluator_review(request, application_id):
    return role_review(request, application_id, 'financial_team_evaluator')

def transaction_commission_review(request, application_id):
    return role_review(request, application_id, 'transaction_commission')

def ceo_review(request, application_id):
    return role_review(request, application_id, 'ceo') 
       