from django import template

register = template.Library()

@register.filter
def div(value, arg):
    """Деление: value / arg"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError):
        return 0

@register.filter
def mul(value, arg):
    """Умножение: value * arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def add(value, arg):
    """Сложение: value + arg"""
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return 0