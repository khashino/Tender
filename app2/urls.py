from django.urls import path
from . import views

app_name = 'app2'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.settings, name='settings'),
    path('settings/upload-document/', views.upload_document, name='upload_document'),
    path('settings/delete-document/<int:document_id>/', views.delete_document, name='delete_document'),
    path('download-document/<int:document_id>/', views.download_document, name='download_document'),
    path('tenders/', views.tender_list, name='tender_list'),
    path('tenders/create/', views.tender_create, name='tender_create'),
    path('tenders/<int:tender_id>/', views.tender_detail, name='tender_detail'),
] 