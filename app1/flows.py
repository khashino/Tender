from viewflow import this
from viewflow.workflow import flow, lock, act
from viewflow.workflow.flow import views
from django.utils import timezone
from django.db import transaction
from viewflow.workflow.models import Task

from .models import TenderApplicationProcess
from shared_models.models import TenderApplication


class TenderApplicationFlow(flow.Flow):
    process_class = TenderApplicationProcess
    app_name = "tender_application"  # Ensure this matches the app name in `Application`
    
    process_title = "Tender Application Review"
    process_description = "Review process for tender applications"

    # Role display names mapping
    ROLE_DISPLAY_NAMES = {
        'purchase_expert': 'کارشناس خرید',
        'team_leader': 'سرپرست خرید',
        'supply_chain_manager': 'مدیر زنجیره تامین',
        'technical_evaluator': 'ارزیاب فنی',
        'financial_deputy': 'معاونت مالی',
        'financial_manager': 'مدیر مالی',
        'commercial_team_evaluator': 'ارزیاب تیم بازرگانی',
        'financial_team_evaluator': 'ارزیاب تیم مالی',
        'transaction_commission': 'کمیسیون معاملات',
        'ceo': 'مدیر عامل',
    }

    # Start the flow when a new application is submitted
    start_noninteractive = flow.StartHandle(this.start_process).Next(this.purchase_expert_review)

    # Initial review step
    purchase_expert_review = (
        flow.View(views.UpdateProcessView.as_view(fields=["notes", "is_approved", "is_rejected"]))
        .Annotation(title="purchase expert review")
        .Permission(auto_create=True)
        .Next(this.check_initial_review)
    )

    # Check the result of the initial review
    check_initial_review = (
        flow.If(lambda activation: activation.process.is_approved)
        .Then(this.team_leader_review)
        .Else(this.check_rejected)
    )

    # Check if the application was rejected
    check_rejected = (
        flow.If(lambda activation: activation.process.is_rejected)
        .Then(this.notify_rejection)
        .Else(this.end)
    )

    # Detailed review for shortlisted applications
    team_leader_review = (
        flow.View(views.UpdateProcessView.as_view(fields=["notes", "is_approved", "is_rejected"]))
        .Annotation(title="team leader review")
        .Permission(auto_create=True)
        .Next(this.check_final_decision)
    )

    # Check the final decision
    check_final_decision = (
        flow.If(lambda activation: activation.process.is_accepted)
        .Then(this.notify_acceptance)
        .Else(this.check_final_rejection)
    )

    # Check if the application was rejected in the final stage
    check_final_rejection = (
        flow.If(lambda activation: activation.process.is_rejected)
        .Then(this.notify_rejection)
        .Else(this.end)
    )

    # Notify the applicant of acceptance
    notify_acceptance = (
        flow.Function(this.send_acceptance_notification)
        .Next(this.end)
    )

    # Notify the applicant of rejection
    notify_rejection = (
        flow.Function(this.send_rejection_notification)
        .Next(this.end)
    )

    # End the flow
    end = flow.End()

    def start_process(self, activation, application_id=None):
        if application_id:
            application = TenderApplication.objects.get(id=application_id)
            activation.process.application = application
            activation.process.save()
        return activation.process

    def handle_role_review(self, process, current_task, role, user, data):
        """
        Handle the role-based review process and create next tasks
        """
        with transaction.atomic():
            # Update process with review data
            process.notes = data.get('notes', '')
            process.is_accepted = data.get('is_accepted', False)
            process.is_rejected = data.get('is_rejected', False)
            process.save()
            
            # Update application status
            application = process.application
            if process.is_rejected:
                application.status = 'rejected'
            elif process.is_accepted:
                application.status = 'accepted'
            else:
                application.status = 'reviewed'
            application.save()
            
            # Complete current task
            current_task.status = 'DONE'
            current_task.finished = timezone.now()
            current_task.owner = user
            current_task.save()
            
            # Create next task based on role and decision
            if role == 'purchase_expert':
                if process.is_accepted:
                    next_task = Task.objects.create(
                        process=process,
                        flow_task=self.team_leader_review,
                        status='NEW',
                        created=timezone.now()
                    )
                else:
                    next_task = Task.objects.create(
                        process=process,
                        flow_task=self.check_rejected,
                        status='NEW',
                        created=timezone.now()
                    )
                next_task.previous.set([current_task])
                
                if process.is_rejected:
                    self._handle_rejection(process, next_task)
            else:
                if process.is_accepted:
                    self._handle_acceptance(process, current_task)
                elif process.is_rejected:
                    self._handle_rejection(process, current_task)
                else:
                    self._create_end_task(process, current_task)
            
            return True

    def _handle_acceptance(self, process, previous_task):
        """Handle acceptance notification and create end task"""
        next_task = Task.objects.create(
            process=process,
            flow_task=self.notify_acceptance,
            status='NEW',
            created=timezone.now()
        )
        next_task.previous.set([previous_task])
        
        try:
            self.send_acceptance_notification(next_task.flow_task.activation_class(next_task))
            next_task.status = 'DONE'
            next_task.finished = timezone.now()
            next_task.save()
            self._create_end_task(process, next_task)
        except Exception as e:
            print(f"Error sending acceptance notification: {str(e)}")

    def _handle_rejection(self, process, previous_task):
        """Handle rejection notification and create end task"""
        next_task = Task.objects.create(
            process=process,
            flow_task=self.notify_rejection,
            status='NEW',
            created=timezone.now()
        )
        next_task.previous.set([previous_task])
        
        try:
            self.send_rejection_notification(next_task.flow_task.activation_class(next_task))
            next_task.status = 'DONE'
            next_task.finished = timezone.now()
            next_task.save()
            self._create_end_task(process, next_task)
        except Exception as e:
            print(f"Error sending rejection notification: {str(e)}")

    def _create_end_task(self, process, previous_task):
        """Create an end task"""
        end_task = Task.objects.create(
            process=process,
            flow_task=self.end,
            status='DONE',
            created=timezone.now(),
            started=timezone.now(),
            finished=timezone.now()
        )
        end_task.previous.set([previous_task])

    def send_acceptance_notification(self, activation):
        application = activation.process.application
        if application:
            # Update the application status
            application.status = 'accepted'
            application.save()
            
            # Create a notification for the applicant
            try:
                from app2.models import Message
                
                # Create a notification for the applicant using the correct parameters
                Message.objects.create(
                    receiver=application.applicant.user,
                    subject="Tender Application Accepted",
                    content=f"Your application for '{application.tender.title}' has been accepted!"
                )
                print(f"Acceptance notification created for user {application.applicant.user.username}")
            except Exception as e:
                print(f"Error creating acceptance notification: {str(e)}")

    def send_rejection_notification(self, activation):
        application = activation.process.application
        if application:
            # Update the application status
            application.status = 'rejected'
            application.save()
            
            # Create a notification for the applicant
            try:
                from app2.models import Message
                
                # Create a notification for the applicant using the correct parameters
                Message.objects.create(
                    receiver=application.applicant.user,
                    subject="Tender Application Rejected",
                    content=f"Your application for '{application.tender.title}' has been rejected."
                )
                print(f"Rejection notification created for user {application.applicant.user.username}")
            except Exception as e:
                print(f"Error creating rejection notification: {str(e)}")
           

