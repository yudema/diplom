from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile, Role, Course, CourseTeacher, Lecture, LectureResource, Enrollment, Progress, Test, Question, Answer, Attempt, Certificate, Notification, CourseLog, TrainingRequest, TrainingPlan, Comment
from .forms import CustomUserChangeForm, CustomUserCreationForm

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm

    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_blocked')
    list_display_links = ('username',)
    list_filter = ('role', 'is_blocked')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Личные данные', {'fields': ('first_name', 'last_name')}),
        ('Права и статус', {'fields': ('role', 'is_blocked')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )

    actions = ['block_users', 'unblock_users']

    def block_users(self, request, queryset):
        queryset.update(is_blocked=True)
    block_users.short_description = "Заблокировать выбранных пользователей"

    def unblock_users(self, request, queryset):
        queryset.update(is_blocked=False)
    unblock_users.short_description = "Разблокировать выбранных пользователей"

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

# Регистрируем остальные модели с русскими названиями
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone', 'company')
    list_display_links = ('user',)
    search_fields = ('user__username', 'phone', 'company')
    fieldsets = (
        (None, {'fields': ('user', 'phone', 'company')}),
    )
    labels = {
        'user': 'Пользователь',
        'phone': 'Телефон',
        'company': 'Компания',
    }

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    list_display_links = ('name',)
    search_fields = ('name',)
    fieldsets = (
        (None, {'fields': ('name',)}),
    )
    labels = {
        'name': 'Название',
    }

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'duration', 'level')
    list_display_links = ('title',)
    search_fields = ('title', 'description')
    fieldsets = (
        (None, {'fields': ('title', 'description', 'duration', 'level')}),
    )
    labels = {
        'title': 'Название',
        'description': 'Описание',
        'duration': 'Продолжительность',
        'level': 'Уровень',
    }

@admin.register(CourseTeacher)
class CourseTeacherAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Преподаватель курса'
        verbose_name_plural = 'Преподаватели курсов'

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'order_num')
    list_display_links = ('title',)
    search_fields = ('title',)
    fieldsets = (
        (None, {'fields': ('title', 'order_num')}),
    )
    labels = {
        'title': 'Название',
        'order_num': 'Порядковый номер',
    }

@admin.register(LectureResource)
class LectureResourceAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Ресурс лекции'
        verbose_name_plural = 'Ресурсы лекций'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Запись на курс'
        verbose_name_plural = 'Записи на курсы'

@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Прогресс'
        verbose_name_plural = 'Прогресс'

@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('name', 'difficulty', 'attempts')
    list_display_links = ('name',)
    search_fields = ('name',)
    fieldsets = (
        (None, {'fields': ('name', 'difficulty', 'attempts')}),
    )
    labels = {
        'name': 'Название',
        'difficulty': 'Сложность',
        'attempts': 'Попытки',
    }

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('test', 'question_text', 'question_type')
    list_display_links = ('test',)
    search_fields = ('test__name', 'question_text')
    fieldsets = (
        (None, {'fields': ('test', 'question_text', 'question_type')}),
    )
    labels = {
        'test': 'Тест',
        'question_text': 'Текст вопроса',
        'question_type': 'Тип вопроса',
    }

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer_text', 'is_correct')
    list_display_links = ('question',)
    search_fields = ('question__question_text', 'answer_text')
    fieldsets = (
        (None, {'fields': ('question', 'answer_text', 'is_correct')}),
    )
    labels = {
        'question': 'Вопрос',
        'answer_text': 'Текст ответа',
        'is_correct': 'Правильный ответ',
    }

@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Попытка'
        verbose_name_plural = 'Попытки'

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Сертификат'
        verbose_name_plural = 'Сертификаты'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Уведомление'
        verbose_name_plural = 'Уведомления'

@admin.register(CourseLog)
class CourseLogAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Лог курса'
        verbose_name_plural = 'Логи курсов'

@admin.register(TrainingRequest)
class TrainingRequestAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'Заявка на обучение'
        verbose_name_plural = 'Заявки на обучение'

@admin.register(TrainingPlan)
class TrainingPlanAdmin(admin.ModelAdmin):
    class Meta:
        verbose_name = 'План обучения'
        verbose_name_plural = 'Планы обучения'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'lecture', 'text', 'created_at')
    list_display_links = ('user',)
    search_fields = ('user__username', 'lecture__title', 'text')
    fieldsets = (
        (None, {'fields': ('user', 'lecture', 'text', 'created_at')}),
    )
    labels = {
        'user': 'Пользователь',
        'lecture': 'Лекция',
        'text': 'Текст',
        'created_at': 'Дата создания',
    }
