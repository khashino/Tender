from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from viewflow import jsonstore
from django.utils import timezone
from viewflow.workflow.models import Process
from shared_models.models import TenderApplication

class App1User(AbstractUser):
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='app1_users',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='app1_users',
    )

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.username 
    

class Role(models.Model):
    name = models.CharField(max_length=100, verbose_name='نام نقش')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    permissions = models.ManyToManyField(
        Permission,
        verbose_name='دسترسی‌ها',
        blank=True,
        related_name='roles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'نقش'
        verbose_name_plural = 'نقش‌ها'
        permissions = [
            ('can_manage_roles', 'Can manage roles'),
            ('can_assign_roles', 'Can assign roles to users'),
            ('can_view_all_roles', 'Can view all roles'),
            ('can_export_roles', 'Can export roles'),
        ]

    def __str__(self):
        return self.name

class UserRole(models.Model):
    user = models.ForeignKey(App1User, on_delete=models.CASCADE, related_name='user_roles', verbose_name='کاربر')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='user_roles', verbose_name='نقش')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'نقش کاربر'
        verbose_name_plural = 'نقش‌های کاربران'
        unique_together = ('user', 'role')

    def __str__(self):
        return f"{self.user.username} - {self.role.name}"
    

class TenderApplicationProcess(Process):
    application = models.ForeignKey(TenderApplication, on_delete=models.CASCADE, null=True, blank=True)
    notes = jsonstore.TextField(blank=True, null=True)
    is_shortlisted = jsonstore.BooleanField(default=False)
    is_accepted = jsonstore.BooleanField(default=False)
    is_rejected = jsonstore.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Tender Application Process"
        verbose_name_plural = "Tender Application Processes"    