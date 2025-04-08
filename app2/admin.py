from django.contrib import admin
from .models import (
    App2User, Company, CompanyDocument, 
    Announcement, LatestNews, Message, Notification
)

@admin.register(App2User)
class App2UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'registration_number', 'economic_code', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('name', 'registration_number', 'economic_code', 'national_id')
    raw_id_fields = ('user',)

@admin.register(CompanyDocument)
class CompanyDocumentAdmin(admin.ModelAdmin):
    list_display = ('company', 'document_type', 'upload_date', 'is_verified')
    list_filter = ('document_type', 'is_verified')
    search_fields = ('company__name', 'description')
    raw_id_fields = ('company',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'content')
    ordering = ('-created_at',)

@admin.register(LatestNews)
class LatestNewsAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('title', 'content')
    ordering = ('-created_at',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('receiver', 'subject', 'created_at', 'is_read')
    list_filter = ('is_read',)
    search_fields = ('subject', 'content', 'receiver__username')
    raw_id_fields = ('receiver',)
    ordering = ('-created_at',)

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'notification_type', 'created_at', 'is_active')
    list_filter = ('notification_type', 'is_active')
    search_fields = ('title', 'message')
    ordering = ('-created_at',) 