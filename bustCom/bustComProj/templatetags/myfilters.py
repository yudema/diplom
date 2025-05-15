from django import template
import re

register = template.Library()

@register.filter
def getattr_custom(obj, attr):

    if '__' in attr:
        attrs = attr.split('__')
        value = obj
        
        for a in attrs:
            try:
                value = getattr(value, a)
                if callable(value):
                    value = value()
            except (AttributeError, TypeError):
                return ""
                
        return value
    else:
        try:
            attr_value = getattr(obj, attr)
            if callable(attr_value):
                return attr_value()
            return attr_value
        except (AttributeError, TypeError):
            return ""

@register.filter
def replace_underscores(value):

    if not value:
        return ""
    
    value = re.sub(r'_+', ' ', str(value))
    
    if '__' in value:
        value = value.split('__')[-1]
    
    return value.title()

@register.filter
def get_item(dictionary, key):

    if isinstance(dictionary, dict):
        return dictionary.get(key, key)
    return key 