from django.contrib.auth.decorators import user_passes_test

def role_required(role):
    """Декоратор для проверки роли пользователя"""
    def check_role(user):
        return user.is_authenticated and getattr(user.profile, 'role', None) == role
    return user_passes_test(check_role)