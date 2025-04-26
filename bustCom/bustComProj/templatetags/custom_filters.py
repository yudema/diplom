from django import template
import re

register = template.Library()

@register.filter
def getattr_custom(obj, attr):
    """
    Возвращает значение атрибута объекта, поддерживает вложенные атрибуты.
    Например: getattr_custom(obj, 'profile__role')
    """
    if '__' in attr:
        # Если атрибут содержит '__', обрабатываем его как вложенный атрибут
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
        # Обычный атрибут
        try:
            attr_value = getattr(obj, attr)
            if callable(attr_value):
                return attr_value()
            return attr_value
        except (AttributeError, TypeError):
            return ""

@register.filter
def replace_underscores(value):
    """
    Заменяет подчеркивания на пробелы и делает каждое слово с заглавной буквы.
    Например: 'first_name' -> 'First Name'
    """
    if not value:
        return ""
    
    # Заменяем подчеркивания на пробелы
    value = re.sub(r'_+', ' ', str(value))
    
    # Для полей с двойным подчеркиванием (profile__role) берем только часть после последнего __
    if '__' in value:
        value = value.split('__')[-1]
    
    # Делаем первую букву каждого слова заглавной
    return value.title()
