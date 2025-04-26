from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен!")
        email = self.normalize_email(email)  
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('hr', 'HR-менеджер'),
        ('teacher', 'Преподаватель'),
        ('training_manager', 'Менеджер по обучению'),
        ('employee', 'Сотрудник')
    ]

    
    email = models.EmailField(unique=True)  
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')

    objects = UserManager()  

    groups = models.ManyToManyField(
        'auth.Group',
        related_name="bustcomproj_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name="bustcomproj_user_permissions",
        blank=True
    )

    def is_hr(self):
        return self.role == 'hr'

    def is_teacher(self):
        return self.role == 'teacher'

    def is_training_manager(self):
        return self.role == 'training_manager'

    def is_employee(self):
        return self.role == 'employee'

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username






class Course(models.Model):
    LEVEL_CHOICES = [
        ('beginner', 'Начальный'),
        ('intermediate', 'Средний'),
        ('advanced', 'Продвинутый')
    ]
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    duration = models.IntegerField(help_text='Продолжительность в часах')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='beginner')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title



class CourseTeacher(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('course', 'teacher')



class Lecture(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    order_num = models.IntegerField()

    def __str__(self):
        return self.title



class LectureResource(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    resource_type = models.CharField(max_length=10, choices=[('file', 'Файл'), ('video', 'Видео')])
    resource_path = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.lecture.title} - {self.resource_type}"


class Enrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status_choices = [('в процессе', 'В процессе'), ('завершён', 'Завершён'), ('отчислен', 'Отчислен')]
    status = models.CharField(max_length=15, choices=status_choices, default='в процессе')



class Progress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(null=True, blank=True)


class Test(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    difficulty_choices = [('низкая', 'Низкая'), ('средняя', 'Средняя'), ('высокая', 'Высокая')]
    difficulty = models.CharField(max_length=10, choices=difficulty_choices)
    attempts = models.IntegerField(default=3)

    def __str__(self):
        return self.name



class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type_choices = [('один', 'Один ответ'), ('несколько', 'Несколько ответов'), ('ввод', 'Ввод текста')]
    question_type = models.CharField(max_length=10, choices=question_type_choices)



class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_text = models.TextField()
    is_correct = models.BooleanField()



class Attempt(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    attempt_num = models.IntegerField()
    score = models.IntegerField()
    passed = models.BooleanField()
    completed_at = models.DateTimeField(auto_now_add=True)


class Certificate(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    issued_at = models.DateField(auto_now_add=True)
    grade = models.CharField(max_length=10)


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    message = models.TextField()
    status_choices = [('новое', 'Новое'), ('прочитано', 'Прочитано')]
    status = models.CharField(max_length=10, choices=status_choices, default='новое')
    created_at = models.DateTimeField(auto_now_add=True)


class CourseLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    action_choices = [('запись', 'Запись'), ('прогресс', 'Прогресс'), ('завершение', 'Завершение'), ('сертификат', 'Сертификат')]
    action = models.CharField(max_length=15, choices=action_choices)
    related_id = models.IntegerField(null=True, blank=True)
    log_time = models.DateTimeField(auto_now_add=True)


class CompletedLecture(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lecture')  

    def __str__(self):
        return f"{self.user.username} - {self.lecture.title}"



class Profile(models.Model):
    ROLE_CHOICES = [
    ('admin', 'Администратор'),
    ('hr', 'HR-менеджер'),
    ('teacher', 'Преподаватель'),
    ('training_manager', 'Менеджер по обучению'),
    ('employee', 'Сотрудник')
]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=100, blank=True, null=True)
    has_seen_guide = models.BooleanField(default=False, verbose_name='Просмотрено руководство')

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    

from django.db import models
from django.conf import settings

class TestAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField()
    total_questions = models.IntegerField()
    percentage = models.FloatField()
    attempt_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.test.lecture.title} - {self.percentage}%"



class Comment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.lecture.title} - {self.created_at}"
    


from django.db import models
from django.conf import settings

class TrainingRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Ожидание'),
        ('approved', 'Одобрено'),
        ('rejected', 'Отклонено')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.get_status_display()})"

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile, User

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance, defaults={'role': instance.role})

class TrainingPlan(models.Model):
    """Training plan for employees."""
    STATUS_CHOICES = (
        ('draft', 'Черновик'),
        ('active', 'Активный'),
        ('completed', 'Завершен'),
        ('cancelled', 'Отменен'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    courses = models.ManyToManyField('Course', related_name='training_plans')
    employees = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='assigned_training_plans')
    
    def __str__(self):
        return self.title


class ActivityLog(models.Model):
    """Log of user activities in the system."""
    ACTION_CHOICES = (
        ('запись', 'Запись на курс'),
        ('отчислен', 'Отчисление с курса'),
        ('завершение', 'Завершение курса'),
        ('прогресс', 'Прогресс по курсу'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    details = models.TextField(blank=True, null=True)
    log_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-log_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.log_time.strftime('%d.%m.%Y %H:%M')}"


class UserGuide(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class RecommendationTest(models.Model):
    question = models.TextField()
    options = models.JSONField()  # Словарь с вариантами ответов
    correct_answer = models.CharField(max_length=100)
    skill_category = models.CharField(max_length=50)  # Категория навыка (программирование, дизайн и т.д.)

    def __str__(self):
        return self.question

class UserRecommendationTestResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    test = models.ForeignKey(RecommendationTest, on_delete=models.CASCADE)
    answer = models.CharField(max_length=100)
    is_correct = models.BooleanField()
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'test')

class UserGuideProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    guide = models.ForeignKey(UserGuide, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'guide')

