from django import template

register = template.Library()

@register.filter
def status_color(status):
    color_map = {
        'draft': 'secondary',
        'published': 'primary',
        'closed': 'warning',
        'awarded': 'success',
        'cancelled': 'danger'
    }
    return color_map.get(status, 'secondary') 