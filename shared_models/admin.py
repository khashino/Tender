from django.contrib import admin
from .models import Tender, TenderApplication

@admin.register(Tender)
class TenderAdmin(admin.ModelAdmin):
    list_display = ('title', 'reference_number', 'published_date', 'closing_date', 'status', 'estimated_value', 'currency')
    list_filter = ('status', 'published_date', 'closing_date')
    search_fields = ('title', 'reference_number', 'description')
    date_hierarchy = 'published_date'
    readonly_fields = ('published_date',)
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'reference_number')
        }),
        ('Dates', {
            'fields': ('published_date', 'closing_date')
        }),
        ('Financial Information', {
            'fields': ('estimated_value', 'currency')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )

@admin.register(TenderApplication)
class TenderApplicationAdmin(admin.ModelAdmin):
    list_display = ('tender', 'applicant', 'status', 'price_quote', 'submitted_at', 'updated_at')
    list_filter = ('status', 'submitted_at', 'updated_at')
    search_fields = ('tender__title', 'applicant__name', 'cover_letter')
    raw_id_fields = ('tender', 'applicant')
    readonly_fields = ('submitted_at', 'updated_at')
    date_hierarchy = 'submitted_at'
    fieldsets = (
        ('Application Details', {
            'fields': ('tender', 'applicant', 'cover_letter', 'price_quote')
        }),
        ('Documents', {
            'fields': ('proposal_document', 'additional_document')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('submitted_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
