from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import App1User, Role, UserRole, TenderApplicationProcess

@admin.register(App1User)
class App1UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active', 'groups')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'get_name_display', 'created_at', 'updated_at')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    filter_horizontal = ('permissions',)
    readonly_fields = ('created_at', 'updated_at')

    def get_name_display(self, obj):
        return obj.get_name_display()
    get_name_display.short_description = 'نام نقش'

@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('user__username', 'role__name')
    raw_id_fields = ('user', 'role')
    readonly_fields = ('created_at',)

@admin.register(TenderApplicationProcess)
class TenderApplicationProcessAdmin(admin.ModelAdmin):
    list_display = ('id', 'application', 'is_shortlisted', 'is_accepted', 'is_rejected', 'created')
    list_filter = ('is_shortlisted', 'is_accepted', 'is_rejected', 'created')
    search_fields = ('application__id', 'notes')
    raw_id_fields = ('application',)
    readonly_fields = ('created',) 