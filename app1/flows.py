from viewflow import this
from viewflow.workflow import flow, lock, act
from viewflow.workflow.flow import views

from .models import TenderApplicationProcess
from shared_models.models import TenderApplication


class TenderApplicationFlow(flow.Flow):
    process_class = TenderApplicationProcess
    app_name = "tender_application"  # Ensure this matches the app name in `Application`
    
    process_title = "Tender Application Review"
    process_description = "Review process for tender applications"

    

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
                # Message model expects: receiver, subject, content fields
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
                # Message model expects: receiver, subject, content fields
                Message.objects.create(
                    receiver=application.applicant.user,
                    subject="Tender Application Rejected",
                    content=f"Your application for '{application.tender.title}' has been rejected."
                )
                print(f"Rejection notification created for user {application.applicant.user.username}")
            except Exception as e:
                print(f"Error creating rejection notification: {str(e)}")
           

