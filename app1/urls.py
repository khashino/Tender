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
] 