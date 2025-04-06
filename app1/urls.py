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
    path('tender/create/', views.create_tender, name='create_tender'),
    path('tender/applications/', views.tender_applications, name='tender_applications'),
    path('tender/applications/<int:application_id>/review/', views.review_application, name='review_application'),
    path('tender/applications/<int:application_id>/start-workflow/', views.start_application_workflow, name='start_application_workflow'),
] 