from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import FileExtensionValidator
import os
from django.conf import settings

def company_logo_path(instance, filename):
    # Create the directory if it doesn't exist
    path = os.path.join('media','app2', instance.user.username, 'logo')
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    os.makedirs(full_path, exist_ok=True)
    return os.path.join(path, filename)

def company_document_path(instance, filename):
    # Create the directory if it doesn't exist
    path = os.path.join('media','app2', instance.company.user.username, 'documents')
    full_path = os.path.join(settings.MEDIA_ROOT, path)
    os.makedirs(full_path, exist_ok=True)
    return os.path.join(path, filename)

class App2User(AbstractUser):
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='app2_users',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='app2_users',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = 'app2_users'
        verbose_name = 'App2 User'
        verbose_name_plural = 'App2 Users'

    def __str__(self):
        return self.username

class Company(models.Model):
    user = models.OneToOneField(App2User, on_delete=models.CASCADE, related_name='company')
    name = models.CharField(max_length=200, verbose_name='نام شرکت')
    registration_number = models.CharField(max_length=50, verbose_name='شماره ثبت')
    economic_code = models.CharField(max_length=50, verbose_name='کد اقتصادی')
    national_id = models.CharField(max_length=50, verbose_name='شناسه ملی')
    phone = models.CharField(max_length=20, verbose_name='شماره تماس')
    address = models.TextField(verbose_name='آدرس')
    website = models.URLField(blank=True, null=True, verbose_name='وبسایت')
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    logo = models.ImageField(upload_to=company_logo_path, blank=True, null=True, verbose_name='لوگو')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False, verbose_name='تایید شده')

    class Meta:
        verbose_name = 'شرکت'
        verbose_name_plural = 'شرکت‌ها'

    def __str__(self):
        return self.name

class CompanyDocument(models.Model):
    DOCUMENT_TYPES = (
        ('registration', 'آگهی تأسیس'),
        ('statute', 'اساسنامه'),
        ('license', 'پروانه کسب'),
        ('tax', 'گواهی مالیات بر ارزش افزوده'),
        ('insurance', 'گواهی بیمه'),
        ('other', 'سایر'),
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='documents')
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES, verbose_name='نوع سند')
    file = models.FileField(
        upload_to=company_document_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png'])],
        verbose_name='فایل'
    )
    description = models.TextField(blank=True, null=True, verbose_name='توضیحات')
    upload_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False, verbose_name='تایید شده')

    class Meta:
        verbose_name = 'سند شرکت'
        verbose_name_plural = 'اسناد شرکت'

    def __str__(self):
        return f"{self.company.name} - {self.get_document_type_display()}" 