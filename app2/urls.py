from django.urls import path
from . import views

app_name = 'app2'

urlpatterns = [
    path('', views.home, name='home'),
    # path('tenders/', views.tender_list, name='tender_list'),  # Commented out due to dependency
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('settings/', views.settings, name='settings'),
    path('settings/upload-document/', views.upload_document, name='upload_document'),
    path('settings/delete-document/<int:document_id>/', views.delete_document, name='delete_document'),
    path('download-document/<int:document_id>/', views.download_document, name='download_document'),
    
    # Tender Applications - Oracle based
    path('tender-applications/', views.tender_applications, name='tender_applications'),
    path('tender/<int:tender_id>/', views.tender_detail, name='tender_detail'),
    path('tender/<int:tender_id>/apply/', views.apply_to_tender, name='apply_to_tender'),
    path('my-applications/', views.my_applications, name='my_applications'),
    path('application/<int:application_id>/', views.application_detail, name='application_detail'),
    
    # New pages
    path('news-announcements/', views.news_announcements, name='news_announcements'),
    path('rules/', views.rules, name='rules'),
    path('faq/', views.faq, name='faq'),
    path('help/', views.help, name='help'),
    
    
] 