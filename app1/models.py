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
    ROLE_CHOICES = [
        ('purchase_expert', 'کارشناس خرید'),
        ('team_leader', 'سرپرست خرید'),
        ('supply_chain_manager', 'مدیر زنجیره تامین'),
        ('technical_evaluator', 'ارزیاب فنی'),
        ('financial_deputy', 'معاونت مالی و ستادی'),
        ('financial_manager', 'مدیر مالی'),
        ('commercial_team_evaluator', 'ارزیاب تیم بازرگانی'),
        ('financial_team_evaluator', 'ارزیاب تیم مالی'),
        ('transaction_commission', 'کمیسیون معاملات'),
        ('ceo', 'مدیر عامل'),
    ]

    # Define permission groups for each role
    ROLE_PERMISSIONS = {
        'purchase_expert': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
        ],
        'team_leader': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_application_approval',
        ],
        'supply_chain_manager': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_application_approval',
            'view_page_supplier_management',
        ],
        'technical_evaluator': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_technical_evaluation',
        ],
        'financial_deputy': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_financial_evaluation',
            'view_page_financial_approval',
        ],
        'financial_manager': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_financial_evaluation',
            'view_page_financial_approval',
            'view_page_budget_management',
        ],
        'commercial_team_evaluator': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_commercial_evaluation',
        ],
        'financial_team_evaluator': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_financial_evaluation',
        ],
        'transaction_commission': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_transaction_approval',
            'view_page_final_decision',
        ],
        'ceo': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_transaction_approval',
            'view_page_final_decision',
            'view_page_role_management',
            'view_page_user_management',
        ],
    }

    name = models.CharField(max_length=100, choices=ROLE_CHOICES, verbose_name='نام نقش')
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
            # Home and Dashboard
            ('view_page_home', 'Can view home page'),
            
            # Tender Related Pages
            ('view_page_tender_applications', 'Can view tender applications page'),
            ('view_page_tender_details', 'Can view tender details page'),
            
            # Company Related Pages
            ('view_page_company_profiles', 'Can view company profiles page'),
            
            # Application Related Pages
            ('view_page_application_review', 'Can view application review page'),
            ('view_page_application_execute', 'Can view application execute page'),
            ('view_page_application_approval', 'Can view application approval page'),
            
            # Evaluation Pages
            ('view_page_technical_evaluation', 'Can view technical evaluation page'),
            ('view_page_financial_evaluation', 'Can view financial evaluation page'),
            ('view_page_commercial_evaluation', 'Can view commercial evaluation page'),
            
            # Approval Pages
            ('view_page_financial_approval', 'Can view financial approval page'),
            ('view_page_transaction_approval', 'Can view transaction approval page'),
            ('view_page_final_decision', 'Can view final decision page'),
            
            # Management Pages
            ('view_page_supplier_management', 'Can view supplier management page'),
            ('view_page_budget_management', 'Can view budget management page'),
            ('view_page_role_management', 'Can view role management page'),
            ('view_page_user_management', 'Can view user management page'),
        ]

    def __str__(self):
        return self.get_name_display()

    def get_name_display(self):
        return dict(self.ROLE_CHOICES).get(self.name, self.name)

    def assign_default_permissions(self):
        """Assign default permissions based on the role"""
        from django.contrib.auth.models import Permission
        from django.contrib.contenttypes.models import ContentType
        
        # Clear existing permissions
        self.permissions.clear()
        
        # Get permissions for this role
        permission_codenames = self.ROLE_PERMISSIONS.get(self.name, [])
        
        # Get all permissions
        permissions = Permission.objects.filter(codename__in=permission_codenames)
        
        # Assign permissions to the role
        self.permissions.add(*permissions)

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