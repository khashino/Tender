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

    def has_role(self, role_name):
        """Check if user has a specific role"""
        return self.user_roles.filter(role__name=role_name).exists()

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
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
            # Additional ViewFlow permissions
            'viewflow.view_flowchart',
            'viewflow.view_flowchart_task',
            'viewflow.view_flowchart_process',
            'viewflow.view_flowchart_flow',
            'viewflow.view_flowchart_flowclass',
            'viewflow.view_flowchart_flowtask',
            'viewflow.view_flowchart_flowtaskmodel',
            'viewflow.view_flowchart_flowtaskmodelproxy',
            'viewflow.view_flowchart_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowchart_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowchart_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowchart_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow admin permissions
            'viewflow.add_process',
            'viewflow.change_process',
            'viewflow.delete_process',
            'viewflow.add_task',
            'viewflow.change_task',
            'viewflow.delete_task',
            'viewflow.add_flow',
            'viewflow.change_flow',
            'viewflow.delete_flow',
            'viewflow.add_flowclass',
            'viewflow.change_flowclass',
            'viewflow.delete_flowclass',
            'viewflow.add_flowtask',
            'viewflow.change_flowtask',
            'viewflow.delete_flowtask',
            'viewflow.add_flowtaskmodel',
            'viewflow.change_flowtaskmodel',
            'viewflow.delete_flowtaskmodel',
            'viewflow.add_flowtaskmodelproxy',
            'viewflow.change_flowtaskmodelproxy',
            'viewflow.delete_flowtaskmodelproxy',
            'viewflow.add_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.change_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.delete_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.add_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.change_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.delete_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.add_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.change_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.delete_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.add_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.change_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.delete_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
        ],
        'team_leader': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_application_approval',
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
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
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
        ],
        'technical_evaluator': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_technical_evaluation',
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
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
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
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
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
        ],
        'commercial_team_evaluator': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_commercial_evaluation',
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
        ],
        'financial_team_evaluator': [
            'view_page_home',
            'view_page_tender_applications',
            'view_page_tender_details',
            'view_page_company_profiles',
            'view_page_application_review',
            'view_page_application_execute',
            'view_page_financial_evaluation',
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
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
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
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
            # ViewFlow permissions
            'viewflow.view_process',
            'viewflow.view_task',
            'viewflow.view_flow',
            'viewflow.view_flowclass',
            'viewflow.view_flowtask',
            'viewflow.view_flowtaskmodel',
            'viewflow.view_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            'viewflow.view_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy_flowtaskmodelproxy',
            # ViewFlow site permissions
            'viewflow.can_view_site',
            'viewflow.can_view_flow',
            'viewflow.can_view_process',
            'viewflow.can_view_task',
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
    is_approved = jsonstore.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Tender Application Process"
        verbose_name_plural = "Tender Application Processes"    

class FlowTemplate(models.Model):
    FLOW_TYPES = [
        ('tender', 'جریان کار مناقصه'),
        ('purchase', 'جریان کار خرید'),
        ('approval', 'جریان کار تایید'),
        ('custom', 'جریان کار سفارشی'),
    ]
    
    name = models.CharField(max_length=100, verbose_name='نام جریان کار')
    description = models.TextField(blank=True, verbose_name='توضیحات')
    flow_type = models.CharField(max_length=20, choices=FLOW_TYPES, default='custom', verbose_name='نوع جریان کار')
    app_name = models.CharField(max_length=50, verbose_name='نام برنامه', help_text='نام برنامه برای استفاده در viewflow')
    process_class = models.CharField(max_length=100, verbose_name='کلاس فرآیند', help_text='نام کلاس فرآیند در models.py')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    code_generated = models.BooleanField(default=False, verbose_name='کد تولید شده')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(App1User, on_delete=models.SET_NULL, null=True, related_name='created_flows')

    class Meta:
        verbose_name = 'قالب جریان کار'
        verbose_name_plural = 'قالب‌های جریان کار'
        permissions = [
            ('create_flow_template', 'Can create flow template'),
            ('edit_flow_template', 'Can edit flow template'),
            ('view_flow_template', 'Can view flow template'),
            ('delete_flow_template', 'Can delete flow template'),
            ('generate_flow_code', 'Can generate flow code'),
        ]

    def __str__(self):
        return self.name

class FlowStep(models.Model):
    STEP_TYPES = [
        ('start', 'شروع'),
        ('end', 'پایان'),
        ('view', 'نمایش فرم'),
        ('function', 'اجرای تابع'),
        ('if', 'شرط'),
        ('split', 'انشعاب'),
        ('join', 'اتصال'),
    ]
    
    CONDITION_TYPES = [
        ('field_check', 'بررسی مقدار فیلد'),
        ('python_code', 'کد پایتون'),
    ]
    
    flow_template = models.ForeignKey(FlowTemplate, on_delete=models.CASCADE, related_name='steps', verbose_name='قالب جریان کار')
    name = models.CharField(max_length=100, verbose_name='نام مرحله')
    step_type = models.CharField(max_length=20, choices=STEP_TYPES, verbose_name='نوع مرحله')
    position = models.PositiveIntegerField(default=0, verbose_name='ترتیب')
    
    # For view steps
    view_class = models.CharField(max_length=100, blank=True, null=True, verbose_name='کلاس نمایش')
    view_fields = models.TextField(blank=True, null=True, verbose_name='فیلدهای فرم (با کاما جدا شود)')
    
    # For function steps
    function_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='نام تابع')
    
    # For if steps
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPES, blank=True, null=True, verbose_name='نوع شرط')
    condition_field = models.CharField(max_length=100, blank=True, null=True, verbose_name='فیلد شرط')
    condition_value = models.CharField(max_length=100, blank=True, null=True, verbose_name='مقدار شرط')
    condition_code = models.TextField(blank=True, null=True, verbose_name='کد شرط')
    
    # Permissions
    permissions = models.CharField(max_length=255, blank=True, null=True, verbose_name='دسترسی‌ها (با کاما جدا شود)')
    auto_create_permission = models.BooleanField(default=True, verbose_name='ایجاد خودکار دسترسی')
    
    # For connections between steps
    next_step = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='previous_steps', verbose_name='مرحله بعدی')
    branch_true = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='if_true_source', verbose_name='مرحله بعدی در صورت درست بودن شرط')
    branch_false = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='if_false_source', verbose_name='مرحله بعدی در صورت نادرست بودن شرط')
    
    # Display settings for the flow designer
    x_coord = models.IntegerField(default=0, verbose_name='موقعیت X')
    y_coord = models.IntegerField(default=0, verbose_name='موقعیت Y')
    
    class Meta:
        verbose_name = 'مرحله جریان کار'
        verbose_name_plural = 'مراحل جریان کار'
        ordering = ['flow_template', 'position']

    def __str__(self):
        return f"{self.flow_template.name} - {self.name}"    