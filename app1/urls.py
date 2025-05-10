from django.urls import path
from . import views

app_name = 'app1'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('company-approvals/', views.company_approvals, name='company_approvals'),
    path('company-approvals/approve/<int:company_id>/', views.approve_company, name='approve_company'),
    path('company-approvals/reject/<int:company_id>/', views.reject_company, name='reject_company'),
    path('roles/', views.role_list, name='role_list'),
    path('roles/create/', views.role_create, name='role_create'),
    path('roles/<int:role_id>/edit/', views.role_edit, name='role_edit'),
    path('roles/<int:role_id>/delete/', views.role_delete, name='role_delete'),
    path('user-roles/', views.user_roles, name='user_roles'),
    path('user-roles/<int:user_id>/assign/', views.assign_user_roles, name='assign_user_roles'),

    # Tender Management
    path('tender/create/', views.create_tender, name='create_tender'),
    path('tender/list/', views.tender_list, name='tender_list'),
    path('tender/applications/', views.tender_applications, name='tender_applications'),
    path('tender/applications/<int:application_id>/review/', views.review_application, name='review_application'),
    path('tender/applications/<int:application_id>/start-workflow/', views.start_application_workflow, name='start_application_workflow'),
    
    # Workflow Steps
    path('tender/applications/<int:application_id>/initial-review/', views.initial_review, name='initial_review'),
    path('tender/applications/<int:application_id>/detailed-review/', views.detailed_review, name='detailed_review'),
    
    # Notification Management
    path('controls/notifications/', views.notification_list, name='notification_list'),
    path('controls/notifications/create/', views.notification_create, name='notification_create'),
    path('controls/notifications/<int:notification_id>/toggle/', views.notification_toggle, name='notification_toggle'),
    path('controls/notifications/<int:notification_id>/delete/', views.notification_delete, name='notification_delete'),
    
    # Participant Management
    path('controls/participants/', views.participant_management, name='participant_management'),
    path('controls/company/<int:company_id>/details/', views.company_details, name='company_details'),

    # Flow Designer
    path('flows/', views.flow_template_list, name='flow_template_list'),
    path('flows/create/', views.flow_template_create, name='flow_template_create'),
    path('flows/<int:template_id>/designer/', views.flow_designer, name='flow_designer'),
    path('flows/<int:template_id>/step/create/', views.flow_step_create, name='flow_step_create'),
    path('flows/step/<int:step_id>/update/', views.flow_step_update, name='flow_step_update'),
    path('flows/step/<int:step_id>/delete/', views.flow_step_delete, name='flow_step_delete'),
    path('flows/connection/update/', views.flow_connection_update, name='flow_connection_update'),
    path('flows/<int:template_id>/generate/', views.generate_flow_code, name='generate_flow_code'),
    path('flows/<int:template_id>/delete/', views.flow_template_delete, name='flow_template_delete'),

    # Role-based review URLs
    path('tender/application/<int:application_id>/purchase-expert-review/', views.purchase_expert_review, name='purchase_expert_review'),
    path('tender/application/<int:application_id>/team-leader-review/', views.team_leader_review, name='team_leader_review'),
    path('tender/application/<int:application_id>/supply-chain-manager-review/', views.supply_chain_manager_review, name='supply_chain_manager_review'),
    path('tender/application/<int:application_id>/technical-evaluator-review/', views.technical_evaluator_review, name='technical_evaluator_review'),
    path('tender/application/<int:application_id>/financial-deputy-review/', views.financial_deputy_review, name='financial_deputy_review'),
    path('tender/application/<int:application_id>/financial-manager-review/', views.financial_manager_review, name='financial_manager_review'),
    path('tender/application/<int:application_id>/commercial-team-evaluator-review/', views.commercial_team_evaluator_review, name='commercial_team_evaluator_review'),
    path('tender/application/<int:application_id>/financial-team-evaluator-review/', views.financial_team_evaluator_review, name='financial_team_evaluator_review'),
    path('tender/application/<int:application_id>/transaction-commission-review/', views.transaction_commission_review, name='transaction_commission_review'),
    path('tender/application/<int:application_id>/ceo-review/', views.ceo_review, name='ceo_review'),
] 