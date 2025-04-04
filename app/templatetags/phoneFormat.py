from django import template

register = template.Library()

@register.filter
def formatUsaPhone(value):
    """
    Convierte 13207889301 → 1 320-788-9301
    """
    value = str(value) 
    
    if not value or len(value) < 11:
        return value

    country = value[0]
    area = value[1:4]
    first = value[4:7]
    last = value[7:]

    return f"+{country} ({area})-{first}-{last}"
