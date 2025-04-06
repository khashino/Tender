from django.db import models
from app2.models import Company

# Create your models here.

class Tender(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    reference_number = models.CharField(max_length=50, unique=True)
    published_date = models.DateTimeField(auto_now_add=True)
    closing_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('closed', 'Closed'),
            ('awarded', 'Awarded'),
            ('cancelled', 'Cancelled')
        ],
        default='draft'
    )
    estimated_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    
    class Meta:
        ordering = ['-published_date']
        
    def __str__(self):
        return f"{self.reference_number} - {self.title}"


def application_directory_path(instance, filename):
    # Files will be uploaded to MEDIA_ROOT/user_<id>/applications/<filename>
    return f"{instance.applicant.user.username}/applications/{filename}"

class TenderApplication(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('shortlisted', 'Shortlisted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]
    
    tender = models.ForeignKey(Tender, on_delete=models.CASCADE, related_name="applications")
    applicant = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="applications")
    cover_letter = models.TextField()
    price_quote = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    proposal_document = models.FileField(upload_to=application_directory_path)
    additional_document = models.FileField(upload_to=application_directory_path, null=True, blank=True)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        # Ensure a company can only apply once to each tender
        unique_together = ('tender', 'applicant')
    
    def __str__(self):
        return f"Application from {self.applicant.company_name} for {self.tender.title}"

