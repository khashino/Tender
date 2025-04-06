from django import template
from shared_models.models import TenderApplication

register = template.Library()

@register.filter
def status_color(status):
    color_map = {
        'pending': 'warning',
        'shortlisted': 'info',
        'accepted': 'success',
        'rejected': 'danger',
    }
    return color_map.get(status, 'secondary') 