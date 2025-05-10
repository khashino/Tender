from django import template
from django.template.defaultfilters import stringfilter
from app1.models import UserRole

register = template.Library()

@register.filter
def status_color(status):
    """Return Bootstrap color class based on status"""
    color_map = {
        'pending': 'warning',
        'shortlisted': 'info',
        'accepted': 'success',
        'rejected': 'danger',
        'reviewed': 'secondary'
    }
    return color_map.get(status, 'secondary')

@register.filter(name='has_role')
def has_role(user, role_name):
    """Check if user has a specific role using the custom UserRole model"""
    try:
        return UserRole.objects.filter(user=user, role__name=role_name).exists()
    except:
        return False 