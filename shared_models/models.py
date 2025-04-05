from django.db import models

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
