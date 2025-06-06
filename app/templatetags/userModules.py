from django import template

register = template.Library()

@register.filter
def has_module(user, module_name):
    if not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.company.modules.filter(name=module_name).exists()

