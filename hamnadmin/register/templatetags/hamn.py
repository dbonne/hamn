from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from django import template

from hamnadmin.util.html import TruncateAndClean

register = template.Library()


@register.filter(name='postcontents')
@stringfilter
def postcontents(value):
    return mark_safe(TruncateAndClean(value))
