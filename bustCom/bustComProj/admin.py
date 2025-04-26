from django.contrib import admin
from .models import (
    Role, User, Course, CourseTeacher, Lecture, LectureResource,
    Enrollment, Progress, Test, Question, Answer, Attempt,
    Certificate, Notification, CourseLog, TrainingRequest, TrainingPlan
)

admin.site.register(Role)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    list_filter = ('role', 'is_staff', 'is_active')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'duration', 'level', 'created_at')
    list_filter = ('level', 'teacher')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)

@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order_num')
    search_fields = ('title',)
    list_filter = ('course',)

admin.site.register([
    LectureResource, CourseTeacher, Enrollment, Progress, Test,
    Question, Answer, Attempt, Certificate, Notification,
    CourseLog, TrainingRequest, TrainingPlan
])
