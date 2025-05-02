from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg, Max, Min, Count, Sum
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, FileResponse
from django.forms import modelform_factory, Form, FileField
import os
import datetime
import sqlite3
import tempfile
import shutil
from django.db.models import Q
from django.utils import timezone
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from PIL import Image, ImageDraw, ImageFont

from .models import (
    User, Role, Course, CourseTeacher, Lecture, LectureResource, Enrollment, Progress,
    Test, Question, Answer, Attempt, Certificate, Notification, CourseLog, CompletedLecture,
    Profile, Comment, TrainingRequest, TestAttempt, TrainingPlan, ActivityLog, UserGuide,
    RecommendationTest, UserRecommendationTestResult, UserGuideProgress
)
from .forms import (
    CustomUserCreationForm, ProfileForm, CommentForm, LectureForm, TestForm, QuestionForm,
    AnswerForm, CourseForm, CustomUserChangeForm
)
from .decorators import role_required
from .telegram_utils import notify_training_request

def role_required(role):
    """Декоратор для проверки роли пользователя"""
    def check_role(user):
        return user.is_authenticated and getattr(user.profile, 'role', '').lower() == role.lower()
    return user_passes_test(check_role)

def roles_required(*roles):
    """Декоратор для проверки нескольких ролей"""
    def check_role(user):
        return user.is_authenticated and getattr(user.profile, 'role', None) in roles
    return user_passes_test(check_role)

MODEL_MAP = {
    'users': get_user_model(),
    'roles': Role,
    'courses': Course,
    'course_teachers': CourseTeacher,
    'lectures': Lecture,
    'lecture_resources': LectureResource,
    'enrollments': Enrollment,
    'progress': Progress,
    'tests': Test,
    'questions': Question,
    'answers': Answer,
    'attempts': Attempt,
    'certificates': Certificate,
    'notifications': Notification,
    'course_logs': CourseLog,
    'completed_lectures': CompletedLecture,
}

TABLES = {
    'users': 'Пользователи',
    'roles': 'Роли',
    'courses': 'Курсы',
    'lectures': 'Лекции',
    'enrollments': 'Записи на курсы',
    'tests': 'Тесты',
    'questions': 'Вопросы',
    'answers': 'Ответы',
    'attempts': 'Попытки тестов',
    'certificates': 'Сертификаты',
}

FIELD_LABELS = {
    'id': 'ID',
    'username': 'Логин',
    'email': 'Email',
    'first_name': 'Имя',
    'last_name': 'Фамилия',
    'profile__role': 'Роль',
    'last_login': 'Последний вход',
    'is_active': 'Статус',
    # Добавьте остальные поля по необходимости
}

ROLE_DASHBOARD = {
    'admin': 'admin_dashboard',
    'teacher': 'teacher_dashboard',
    'hr': 'hr_dashboard',
    'training_manager': 'training_manager_dashboard',
    'employee': 'employee_dashboard',
}

@role_required('admin')
def admin_dashboard(request):
    return render(request, 'admin_panel/dashboard.html', {'tables': TABLES})

@role_required('admin')
def manage_table(request, table_name):
    model = MODEL_MAP.get(table_name)
    if not model:
        return JsonResponse({'error': 'Неверное имя таблицы'}, status=400)

    objects = model._default_manager.all()
    
    # Получаем поля модели
    if table_name == 'users':
        # Для пользователей показываем только важные поля - убрано is_active для более компактного вида
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile__role', 'last_login']
        
        # Если поле profile__role не доступно напрямую, обрабатываем это в шаблоне
        objects = objects.select_related('profile')
    else:
        fields = [field.name for field in model._meta.get_fields() 
                 if not field.is_relation or field.one_to_one or field.many_to_one]
        # Исключаем служебные поля
        fields = [f for f in fields if not (f.startswith('_') or f in ['password', 'logentry'])]
        
    object_values = objects.values_list()

    return render(request, 'admin_panel/manage_table.html', {
        'objects': objects,
        'object_values': object_values,
        'table_name': table_name,
        'fields': fields,
        'field_labels': FIELD_LABELS,
    })

@role_required('admin')
def add_object(request, table_name):
    model = MODEL_MAP.get(table_name)
    if not model:
        return JsonResponse({'error': 'Неверное имя таблицы'}, status=400)

    if table_name == 'users':
        form_class = CustomUserCreationForm
    else:
        form_class = modelform_factory(model, fields="__all__")
    form = form_class()

    if request.method == 'POST':
        form = form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('manage_table', table_name=table_name)

    return render(request, 'admin_panel/add_object.html', {'form': form, 'table_name': table_name, 'TABLES': TABLES})

@role_required('admin')
def edit_object(request, table_name, object_id):
    model = MODEL_MAP.get(table_name)
    if not model:
        return JsonResponse({'error': 'Неверное имя таблицы'}, status=400)

    obj = get_object_or_404(model, pk=object_id)
    if table_name == 'users':
        form_class = CustomUserChangeForm
    else:
        form_class = modelform_factory(model, fields="__all__")
    form = form_class(instance=obj)

    if request.method == 'POST':
        form = form_class(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('manage_table', table_name=table_name)

    return render(request, 'admin_panel/edit_object.html', {'form': form, 'table_name': table_name, 'TABLES': TABLES})

@role_required('admin')
def delete_object(request, table_name, object_id):
    model = MODEL_MAP.get(table_name)
    if not model:
        return JsonResponse({'error': 'Неверное имя таблицы'}, status=400)

    obj = get_object_or_404(model, id=object_id)
    obj.delete()
    return redirect('manage_table', table_name=table_name)

@login_required
@role_required('teacher')
def add_test(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)

    if request.method == 'POST':
        form = TestForm(request.POST)
        if form.is_valid():
            test = form.save(commit=False)
            test.lecture = lecture
            test.save()
            return redirect('lecture_detail', lecture.id)
    else:
        form = TestForm()

    return render(request, 'bustComProj/add_test.html', {'form': form, 'lecture': lecture})

@login_required
@role_required('teacher')
def add_question(request, test_id):
    test = get_object_or_404(Test, id=test_id)

    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.test = test
            question.save()
            return redirect('add_answer', question.id)
    else:
        form = QuestionForm(initial={'test': test})

    return render(request, 'bustComProj/add_question.html', {'form': form, 'test': test})

@login_required
@role_required('teacher')
def add_answer(request, question_id):
    question = get_object_or_404(Question, id=question_id)

    if request.method == "POST":
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.save()
            return redirect('add_answer', question.id)
    else:
        form = AnswerForm(initial={'question': question})

    return render(request, 'bustComProj/add_answer.html', {'form': form, 'question': question})

@login_required
def lecture_test(request, lecture_id, test_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    test = get_object_or_404(Test, id=test_id, lecture=lecture)
    questions = Question.objects.filter(test=test).prefetch_related('answer_set')

    if request.method == "POST":
        score = 0
        total_questions = questions.count()

        for question in questions:
            selected_answer_id = request.POST.get(f"question_{question.id}")
            if selected_answer_id:
                try:
                    selected_answer = Answer.objects.get(id=selected_answer_id)
                    if selected_answer.is_correct:
                        score += 1
                except Answer.DoesNotExist:
                    pass

        percentage = (score / total_questions) * 100 if total_questions > 0 else 0

        TestAttempt.objects.create(
            user=request.user,
            test=test,
            score=score,
            total_questions=total_questions,
            percentage=percentage
        )

        return render(request, 'bustComProj/test_result.html', {
            'lecture': lecture, 'test': test, 'score': score, 'total': total_questions, 'percentage': percentage
        })

    attempts = TestAttempt.objects.filter(user=request.user, test=test).order_by('-attempt_date')
    return render(request, 'bustComProj/lecture_test.html', {
        'lecture': lecture, 'test': test, 'questions': questions, 'attempts': attempts
    })

@login_required
def courses_list(request):
    # Получаем все курсы
    all_courses = Course.objects.all().order_by('title')
    
    # Получаем курсы пользователя
    user_courses = Course.objects.filter(enrollment__user=request.user)
    
    # Получаем рекомендованные курсы на основе результатов теста
    user_skills = UserRecommendationTestResult.objects.filter(
        user=request.user,
        is_correct=True
    ).values_list('test__skill_category', flat=True)
    
    # Если у пользователя есть результаты теста, рекомендуем курсы на их основе
    if user_skills:
        recommended_courses = Course.objects.filter(
            level__in=['beginner', 'intermediate']
        ).exclude(
            enrollment__user=request.user
        )[:5]
    else:
        # Если тест не пройден, рекомендуем начальные курсы
        recommended_courses = Course.objects.filter(
            level='beginner'
        ).exclude(
            enrollment__user=request.user
        )[:5]
    
    return render(request, 'bustComProj/courses_list.html', {
        'all_courses': all_courses,
        'user_courses': user_courses,
        'recommended_courses': recommended_courses
    })

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lectures = Lecture.objects.filter(course=course).order_by('order_num')
    
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    
    return render(request, 'bustComProj/course_detail.html', {
        'course': course,
        'lectures': lectures,
        'is_enrolled': is_enrolled
    })

@login_required
def course_lectures(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lectures = Lecture.objects.filter(course=course).order_by('order_num')
    return render(request, 'bustComProj/course_lectures.html', {'course': course, 'lectures': lectures})

@login_required
def lecture_detail(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    resources = LectureResource.objects.filter(lecture=lecture)
    comments = Comment.objects.filter(lecture=lecture).order_by('-created_at')

    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.lecture = lecture
            comment.save()
            return redirect('lecture_detail', lecture_id=lecture.id)
    else:
        form = CommentForm()

    return render(request, 'bustComProj/lecture_detail.html', {
        'lecture': lecture, 'resources': resources, 'comments': comments, 'form': form
    })

@login_required
@role_required('teacher')
def add_lecture(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = LectureForm(request.POST)
        if form.is_valid():
            lecture = form.save(commit=False)
            lecture.course = course
            lecture.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = LectureForm()

    return render(request, 'bustComProj/add_lecture.html', {'form': form, 'course': course})

@login_required
@role_required('teacher')
def edit_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)

    if request.method == 'POST':
        form = LectureForm(request.POST, instance=lecture)
        if form.is_valid():
            form.save()
            return redirect('lecture_detail', lecture.id)
    else:
        form = LectureForm(instance=lecture)

    return render(request, 'bustComProj/edit_lecture.html', {'form': form, 'lecture': lecture})

@login_required
@role_required('teacher')
def delete_lecture(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)

    if request.method == 'POST':
        course_id = lecture.course.id
        lecture.delete()
        messages.success(request, "Лекция успешно удалена.")
        return redirect('course_lectures', course_id=course_id)

    return render(request, 'bustComProj/delete_lecture.html', {'lecture': lecture})

@login_required
def profile(request):
    user = request.user
    enrollments = Enrollment.objects.filter(user=user).select_related('course')

    progress_data = []
    for enrollment in enrollments:
        course = enrollment.course
        total_lectures = Lecture.objects.filter(course=course).count()
        completed_lectures = CompletedLecture.objects.filter(user=user, lecture__course=course).count()
        progress = int((completed_lectures / total_lectures) * 100) if total_lectures > 0 else 0
        
        progress_data.append({
            'course': course.title,
            'course_id': course.id,
            'progress': progress,
            'total_lectures': total_lectures,
            'completed_lectures': completed_lectures
        })

    return render(request, 'bustComProj/profile.html', {
        'progress_data': progress_data
    })

@login_required
def edit_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, user=request.user)

    return render(request, 'bustComProj/edit_profile.html', {'form': form})

def home(request):
    if request.user.is_authenticated:
        role = request.user.profile.role
        if role == 'hr':
            return redirect('hr_dashboard')
        elif role == 'training_manager':
            return redirect('training_manager_dashboard')
        elif role == 'teacher':
            return redirect('teacher_dashboard')
        elif role == 'employee':
            return redirect('employee_dashboard')
        elif role == 'admin':
            return redirect('admin_dashboard')
    return render(request, 'bustComProj/home.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Регистрация успешна! Теперь войдите в систему.')
            return redirect('login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'bustComProj/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_blocked:
                messages.error(request, 'Ваша учетная запись заблокирована. Пожалуйста, обратитесь к администратору.')
                return render(request, 'bustComProj/login.html')
                
            login(request, user)
            # Get or create profile
            profile, created = Profile.objects.get_or_create(user=user)
            # Only show guide and test for employees who haven't seen it
            if profile.role == 'employee' and not profile.has_seen_guide:
                return redirect('first_login_guide')
            return redirect('dashboard_redirect')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')

    return render(request, 'bustComProj/login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    # Если пользователь не сотрудник, используем старую логику
    if request.user.profile.role != 'employee':
        enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)
        if created:
            messages.success(request, f"Вы успешно записались на курс: {course.title}")
        else:
            messages.info(request, f"Вы уже записаны на этот курс!")
    else:
        # Проверка на существующую заявку
        existing_request = TrainingRequest.objects.filter(
            user=request.user, 
            course=course, 
            status__in=['pending', 'approved']
        ).exists()
        
        # Проверка на существующую запись
        already_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
        
        if already_enrolled:
            messages.info(request, f"Вы уже записаны на этот курс!")
        elif existing_request:
            messages.info(request, f"Вы уже подали заявку на этот курс!")
        else:
            # Создаем заявку на обучение
            training_request = TrainingRequest.objects.create(
                user=request.user,
                course=course,
                reason="Заявка от сотрудника"
            )
            # Отправляем уведомление в Telegram
            notify_training_request(training_request)
            messages.success(request, f"Заявка на курс '{course.title}' успешно отправлена и ожидает подтверждения.")

    return redirect('course_detail', course_id=course.id)

@login_required
def mark_lecture_complete(request, lecture_id):
    lecture = get_object_or_404(Lecture, id=lecture_id)
    CompletedLecture.objects.get_or_create(user=request.user, lecture=lecture)
    check_course_completion(request.user, lecture.course)
    return redirect('lecture_detail', lecture_id=lecture.id)

def check_course_completion(user, course):
    total_lectures = Lecture.objects.filter(course=course).count()
    completed_lectures = CompletedLecture.objects.filter(user=user, lecture__course=course).count()

    if total_lectures > 0 and total_lectures == completed_lectures:
        Certificate.objects.get_or_create(user=user, course=course)

@login_required
def dashboard_view(request):
    role = request.user.profile.role
    role_to_template = {
        "admin": "dashboards/admin_dashboard.html",
        "teacher": "dashboards/teacher_dashboard.html",
        "hr": "dashboards/hr_dashboard.html",
        "training_manager": "dashboards/training_manager_dashboard.html",
        "employee": "dashboards/employee_dashboard.html",
    }
    template = role_to_template.get(role, "dashboards/employee_dashboard.html")
    return render(request, template)

@login_required
@role_required('employee')
def employee_dashboard(request):
    # Получаем курсы пользователя
    user_courses = Course.objects.filter(enrollment__user=request.user)
    
    # Собираем статистику по курсам
    completed_courses_count = 0
    total_courses = user_courses.count()
    
    courses_with_progress = []
    total_tests_taken = 0
    total_score_sum = 0
    total_attempts = 0
    
    for course in user_courses:
        # Вычисляем прогресс по лекциям
        total_lectures = Lecture.objects.filter(course=course).count()
        if total_lectures > 0:
            completed_lectures = CompletedLecture.objects.filter(
                user=request.user, 
                lecture__course=course
            ).count()
            progress_percentage = int((completed_lectures / total_lectures) * 100) if total_lectures > 0 else 0
            
            if progress_percentage == 100:
                completed_courses_count += 1
        else:
            progress_percentage = 0
            completed_lectures = 0
        
        # Собираем информацию о тестах
        course_tests = Test.objects.filter(lecture__course=course)
        course_test_attempts = TestAttempt.objects.filter(
            user=request.user,
            test__in=course_tests
        )
        
        course_total_attempts = course_test_attempts.count()
        total_tests_taken += course_total_attempts
        
        # Суммируем баллы для подсчета среднего
        if course_total_attempts > 0:
            course_score_sum = course_test_attempts.aggregate(Sum('score'))['score__sum'] or 0
            total_score_sum += course_score_sum
            total_attempts += course_total_attempts
        
        # Создаем объект с данными курса и его прогрессом
        course_data = {
            'course': course,
            'progress_percentage': progress_percentage,
            'completed_lectures': completed_lectures,
            'total_lectures': total_lectures
        }
        courses_with_progress.append(course_data)
    
    # Вычисляем средний балл
    avg_score = round(total_score_sum / total_attempts, 1) if total_attempts > 0 else 0
    
    context = {
        'courses_with_progress': courses_with_progress,
        'completed_courses_count': completed_courses_count,
        'total_courses': total_courses,
        'avg_score': avg_score,
        'total_tests_taken': total_tests_taken
    }
    
    return render(request, 'dashboards/employee_dashboard.html', context)

@login_required
@role_required('teacher')
def teacher_dashboard(request):
    return render(request, 'dashboards/teacher_dashboard.html')

@login_required
@role_required('hr')
def hr_dashboard(request):
    """HR manager's dashboard."""
    # Получаем последние активности из логов
    recent_activities = ActivityLog.objects.all().order_by('-log_time')[:10]
    
    context = {
        'recent_activities': recent_activities,
    }
    return render(request, 'hr/dashboard.html', context)

@login_required
def training_manager_dashboard(request):
    if request.user.profile.role != 'training_manager':
        return redirect('home')
    return render(request, 'training_manager/dashboard.html')

@login_required
@roles_required('teacher', 'admin')
def create_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            messages.success(request, 'Курс успешно создан!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm()
    
    return render(request, 'courses/create_course.html', {
        'form': form,
        'title': 'Создать новый курс'
    })

@login_required
@roles_required('teacher', 'admin')
def edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Курс обновлён!')
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/edit_course.html', {'form': form, 'course': course})

@login_required
@roles_required('teacher', 'admin')
def delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, 'Курс удалён!')
    return redirect('courses_list')

@login_required
def test_difficulty(request):
    if request.user.profile.role != 'training_manager':
        return redirect('home')
    tests = Test.objects.all()
    return render(request, "training/test_difficulty.html", {"tests": tests})

@login_required
def review_requests(request):
    if request.user.profile.role != 'training_manager':
        return redirect('home')
        
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        training_request = get_object_or_404(TrainingRequest, id=request_id)

        if action == 'approve':
            training_request.status = 'approved'
            # При одобрении заявки автоматически создаем запись о зачислении
            Enrollment.objects.get_or_create(
                user=training_request.user,
                course=training_request.course
            )
            messages.success(request, f"Заявка одобрена! Пользователь зачислен на курс '{training_request.course.title}'")
        elif action == 'reject':
            training_request.status = 'rejected'
            messages.info(request, f"Заявка отклонена!")

        training_request.save()

    requests = TrainingRequest.objects.all().select_related('user', 'course').order_by('-created_at')
    return render(request, 'training_manager/review_requests.html', {'requests': requests})

@login_required
@role_required('training_manager')
def create_training_plan(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            plan_id = request.POST.get('plan_id')
            try:
                plan = TrainingPlan.objects.get(id=plan_id)
                plan.delete()
                messages.success(request, 'План обучения успешно удален')
            except TrainingPlan.DoesNotExist:
                messages.error(request, 'План обучения не найден')
        else:
            title = request.POST.get('title')
            description = request.POST.get('description')
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            status = request.POST.get('status', 'draft')  # Получаем статус, по умолчанию 'draft'
            courses = request.POST.getlist('courses')
            employees = request.POST.getlist('employees')
            
            # Проверяем, что обязательные поля не пустые
            if not title or not description or not start_date or not end_date:
                messages.error(request, 'Пожалуйста, заполните все обязательные поля')
                return redirect('create_training_plan')
            
            try:
                plan = TrainingPlan.objects.create(
                    title=title,
                    description=description,
                    start_date=start_date,
                    end_date=end_date,
                    status=status,  # Добавляем статус в создание плана
                    created_by=request.user
                )
                
                # Добавляем курсы, если они выбраны
                if courses:
                    # Преобразуем строковые ID в целые числа
                    course_ids = [int(course_id) for course_id in courses]
                    plan.courses.set(course_ids)
                
                # Добавляем сотрудников, если они выбраны
                if employees:
                    # Преобразуем строковые ID в целые числа
                    employee_ids = [int(employee_id) for employee_id in employees]
                    plan.employees.set(employee_ids)
                
                messages.success(request, 'План обучения успешно создан')
            except Exception as e:
                messages.error(request, f'Ошибка при создании плана: {str(e)}')
    
    courses = Course.objects.all()
    employees = get_user_model().objects.filter(profile__role='employee')
    training_plans = TrainingPlan.objects.all().order_by('-created_at')
    
    return render(request, 'training_manager/create_training_plan.html', {
        'courses': courses,
        'employees': employees,
        'training_plans': training_plans
    })

@login_required
@role_required('training_manager')
def edit_training_plan(request, plan_id):
    plan = get_object_or_404(TrainingPlan, id=plan_id)
    
    if request.method == 'POST':
        # Проверка и получение всех необходимых данных формы
        title = request.POST.get('title')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        status = request.POST.get('status', 'draft')
        courses = request.POST.getlist('courses')
        employees = request.POST.getlist('employees')
        
        # Проверяем, что обязательные поля не пустые
        if not title or not description or not start_date or not end_date:
            messages.error(request, 'Пожалуйста, заполните все обязательные поля')
            return redirect('edit_training_plan', plan_id=plan_id)
        
        try:
            # Обновляем данные плана
            plan.title = title
            plan.description = description
            plan.start_date = start_date
            plan.end_date = end_date
            plan.status = status
            plan.save()  # Сохраняем изменения в базе данных
            
            # Обновляем связанные курсы и сотрудников
            plan.courses.clear()  # Удаляем старые связи с курсами
            if courses:  # Проверяем, что список курсов не пустой
                # Преобразуем строковые ID в целые числа
                course_ids = [int(course_id) for course_id in courses]
                plan.courses.set(course_ids)  # Устанавливаем новые связи
            
            plan.employees.clear()  # Удаляем старые связи с сотрудниками
            if employees:  # Проверяем, что список сотрудников не пустой
                # Преобразуем строковые ID в целые числа
                employee_ids = [int(employee_id) for employee_id in employees]
                plan.employees.set(employee_ids)  # Устанавливаем новые связи
            
            messages.success(request, 'План обучения успешно обновлен')
            return redirect('create_training_plan')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении плана: {str(e)}')
            return redirect('edit_training_plan', plan_id=plan_id)
    
    # Получаем данные для формы
    courses = Course.objects.all()
    employees = get_user_model().objects.filter(profile__role='employee')
    
    return render(request, 'training_manager/edit_training_plan.html', {
        'plan': plan,
        'courses': courses,
        'employees': employees
    })

def conduct_training(request):
    return render(request, 'training/conduct_training.html')

@login_required
def dashboard_redirect(request):
    role_dashboard = {
        'admin': 'admin_dashboard',
        'teacher': 'teacher_dashboard',
        'hr': 'hr_dashboard',
        'training_manager': 'training_manager_dashboard',
        'employee': 'employee_dashboard',
    }

    user_role = getattr(request.user, 'role', 'employee').lower()

    return redirect(role_dashboard.get(user_role, 'employee_dashboard'))

@login_required
@role_required('teacher')
def answer_questions(request):
    questions = Question.objects.all()

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        answer_text = request.POST.get('answer_text')

        question = get_object_or_404(Question, id=question_id)
        Answer.objects.create(question=question, answer_text=answer_text, is_correct=False)

        messages.success(request, 'Ответ отправлен!')
        return redirect('answer_questions')

    return render(request, 'questions/answer_questions.html', {'questions': questions})

@login_required
@role_required('teacher')
def view_feedback(request):
    feedbacks = Comment.objects.all()
    return render(request, 'teacher/view_feedback.html', {'feedbacks': feedbacks})

@login_required
def track_performance(request):
    if request.user.profile.role != 'hr':
        return redirect('home')
    avg_score = TestAttempt.objects.aggregate(Avg('score'))['score__avg'] or 0
    max_score = TestAttempt.objects.aggregate(Max('score'))['score__max'] or 0
    min_score = TestAttempt.objects.aggregate(Min('score'))['score__min'] or 0

    score_distribution = (
        TestAttempt.objects.values('score')
        .annotate(count=Count('score'))
        .order_by('score')
    )

    scores = [entry['score'] for entry in score_distribution]
    counts = [entry['count'] for entry in score_distribution]

    context = {
        'avg_score': round(avg_score, 2),
        'max_score': max_score,
        'min_score': min_score,
        'scores': scores,
        'counts': counts
    }
    return render(request, 'bustComProj/track_performance.html', context)

@login_required
@role_required('hr')
def evaluate_training(request):
    return render(request, 'hr/evaluate_training.html')

@login_required
@role_required('hr')
def training_evaluation(request):
    return render(request, 'hr/training_evaluation.html')

@login_required
@roles_required('training_manager')
def employee_progress(request):
    employees = get_user_model().objects.filter(profile__role='employee')
    progress_data = []

    for employee in employees:
        enrollments = Enrollment.objects.filter(user=employee)
        data = []
        for enrollment in enrollments:
            total = Lecture.objects.filter(course=enrollment.course).count()
            completed = CompletedLecture.objects.filter(user=employee, lecture__course=enrollment.course).count()
            progress = (completed / total) * 100 if total > 0 else 0
            data.append({'course': enrollment.course, 'progress': progress})

        progress_data.append({'employee': employee, 'courses': data})

    return render(request, 'training_manager/progress.html', {'progress_data': progress_data})

def service(request):
    return render(request, 'service.html')

def manage_users(request):
    return render(request, 'manage_users.html') 

@login_required
def start_training(request):
    return render(request, 'training/start_training.html')

@login_required
def my_certificates(request):
    certificates = Certificate.objects.filter(user=request.user).select_related('course')
    return render(request, 'certificates/my_certificates.html', {'certificates': certificates})

@login_required
@role_required('hr')  
def view_certificates(request):
    certificates = Certificate.objects.all().select_related('user', 'course')
    return render(request, 'certificates/view_certificates.html', {'certificates': certificates})

@login_required
def download_certificate(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user)
    
    # Получаем полное имя пользователя
    user_full_name = f"{certificate.user.first_name} {certificate.user.last_name}".strip()
    if not user_full_name:  # Если имя пустое, используем username
        user_full_name = certificate.user.username
    
    # Создаем изображение (A4 landscape в пикселях при 300 DPI)
    width = int(11.69 * 300)  # A4 width in inches * 300 DPI
    height = int(8.27 * 300)  # A4 height in inches * 300 DPI
    
    # Создаем новое изображение с темным фоном
    image = Image.new('RGB', (width, height), '#1a1a1a')  # Темно-серый фон
    draw = ImageDraw.Draw(image)
    
    # Рисуем декоративную рамку
    border_width = 5
    cyan_color = '#00FFFF'  # Голубой цвет
    
    # Внешняя рамка (голубая)
    draw.rectangle(
        [(border_width, border_width), (width - border_width, height - border_width)],
        outline=cyan_color,
        width=border_width
    )
    
    # Внутренняя рамка
    margin = 50
    draw.rectangle(
        [(margin, margin), (width - margin, height - margin)],
        outline=cyan_color,
        width=2
    )
    
    try:
        # Попытка использовать системный шрифт Arial
        title_font_size = 120
        normal_font_size = 70
        small_font_size = 50
        name_font_size = 100  # Увеличили размер шрифта для имени
        
        title_font = ImageFont.truetype("arial.ttf", title_font_size)
        normal_font = ImageFont.truetype("arial.ttf", normal_font_size)
        small_font = ImageFont.truetype("arial.ttf", small_font_size)
        name_font = ImageFont.truetype("arial.ttf", name_font_size)
    except:
        # Если Arial недоступен, используем дефолтный шрифт
        title_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
    
    # Функция для центрирования текста
    def get_text_position(text, font, y_position):
        text_width = font.getlength(text)
        return ((width - text_width) // 2, y_position)
    
    # Добавляем декоративные линии
    line_y = 180
    line_length = 400
    # Левая линия
    draw.line([(width//2 - line_length, line_y), (width//2 - 100, line_y)], 
              fill=cyan_color, width=3)
    # Правая линия
    draw.line([(width//2 + 100, line_y), (width//2 + line_length, line_y)], 
              fill=cyan_color, width=3)
    
    # Добавляем текст
    # Заголовок (белый)
    draw.text(get_text_position("СЕРТИФИКАТ", title_font, 200), 
             "СЕРТИФИКАТ", fill='white', font=title_font)
    draw.text(get_text_position("об окончании курса", normal_font, 350), 
             "об окончании курса", fill='white', font=normal_font)
    
    # Номер сертификата (голубой)
    cert_number = f"№ {certificate.id}"
    draw.text(get_text_position(cert_number, small_font, 450), 
             cert_number, fill=cyan_color, font=small_font)
    
    # Основной текст (белый)
    draw.text(get_text_position("Настоящим подтверждается, что", normal_font, 600),
             "Настоящим подтверждается, что", fill='white', font=normal_font)
    
    # Имя участника (голубой, крупный шрифт)
    print(f"Rendering name: {user_full_name}")  # Отладочный вывод
    draw.text(get_text_position(user_full_name, name_font, 700),
             user_full_name, fill=cyan_color, font=name_font)
    
    # Текст о завершении (белый)
    draw.text(get_text_position("успешно завершил(а) курс", normal_font, 850),
             "успешно завершил(а) курс", fill='white', font=normal_font)
    
    # Название курса (голубой)
    draw.text(get_text_position(certificate.course.title, normal_font, 950),
             certificate.course.title, fill=cyan_color, font=normal_font)
    
    # Дата (белый)
    date_text = f"Дата выдачи: {certificate.issued_at.strftime('%d.%m.%Y')}"
    draw.text(get_text_position(date_text, small_font, 1100),
             date_text, fill='white', font=small_font)
    
    # Сохраняем изображение в буфер
    buffer = BytesIO()
    image.save(buffer, format='PNG', quality=95)
    buffer.seek(0)
    
    # Отправляем файл
    response = HttpResponse(content_type='image/png')
    response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.id}.png"'
    response.write(buffer.getvalue())
    
    return response

@login_required
def view_certificate(request, certificate_id):
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user)
    return render(request, 'certificates/view_certificate.html', {'certificate': certificate})

@login_required
@role_required('teacher')
def add_lecture_material(request):
    if request.method == 'POST':
        lecture_id = request.POST.get('lecture')
        resource_type = request.POST.get('resource_type')
        resource_path = request.POST.get('resource_path')

        # Проверяем, что все поля заполнены
        if not all([lecture_id, resource_type, resource_path]):
            messages.error(request, 'Пожалуйста, заполните все поля')
        else:
            try:
                lecture = Lecture.objects.get(id=lecture_id)
                if lecture.course.teacher != request.user:
                    messages.error(request, 'У вас нет прав для добавления материалов к этой лекции')
                else:
                    LectureResource.objects.create(
                        lecture=lecture,
                        resource_type=resource_type,
                        resource_path=resource_path
                    )
                    messages.success(request, 'Материал успешно добавлен')
                    return redirect('lecture_detail', lecture_id=lecture.id)
            except Lecture.DoesNotExist:
                messages.error(request, 'Лекция не найдена')

        # Получаем список лекций для формы
        courses = Course.objects.filter(teacher=request.user)
        lectures = Lecture.objects.filter(course__in=courses).order_by('course__title', 'order_num')

        return render(request, 'bustComProj/add_lecture_material.html', {
            'lectures': lectures,
            'title': 'Добавить материал к лекции'
        })
    else:
        courses = Course.objects.filter(teacher=request.user)
        lectures = Lecture.objects.filter(course__in=courses).order_by('course__title', 'order_num')
        return render(request, 'bustComProj/add_lecture_material.html', {
            'lectures': lectures,
            'title': 'Добавить материал к лекции'
        })

@login_required
@role_required('hr')
def assign_courses(request):
    """Assign courses to employees."""
    User = get_user_model()
    employees = User.objects.filter(profile__role='employee')
    courses = Course.objects.all()
    
    if request.method == 'POST':
        if 'action' in request.POST and request.POST['action'] == 'delete':
            # Удаление назначения
            enrollment_id = request.POST.get('enrollment_id')
            try:
                enrollment = Enrollment.objects.get(id=enrollment_id)
                user = enrollment.user
                course = enrollment.course
                enrollment.delete()
                
                # Добавляем запись в журнал активностей
                ActivityLog.objects.create(
                    user=user,
                    course=course,
                    action='отчислен',
                    details=f"HR-менеджер {request.user.username} отчислил с курса"
                )
                
                messages.success(request, f'Назначение курса для {user.username} успешно удалено.')
            except Enrollment.DoesNotExist:
                messages.error(request, 'Назначение не найдено.')
        
        elif 'action' in request.POST and request.POST['action'] == 'update_status':
            # Обновление статуса
            enrollment_id = request.POST.get('enrollment_id')
            new_status = request.POST.get('status')
            
            try:
                enrollment = Enrollment.objects.get(id=enrollment_id)
                old_status = enrollment.status
                enrollment.status = new_status
                enrollment.save()
                
                # Определяем тип действия в зависимости от статуса
                action_type = 'завершение' if new_status == 'завершён' else 'прогресс' if new_status == 'в процессе' else 'отчислен'
                
                # Добавляем запись в журнал активностей
                ActivityLog.objects.create(
                    user=enrollment.user,
                    course=enrollment.course,
                    action=action_type,
                    details=f"HR-менеджер {request.user.username} изменил статус с '{old_status}' на '{new_status}'"
                )
                
                messages.success(request, f'Статус курса для {enrollment.user.username} обновлен на "{new_status}".')
            except Enrollment.DoesNotExist:
                messages.error(request, 'Назначение не найдено.')
        
        else:
            # Новое назначение
            employee_id = request.POST.get('employee')
            course_id = request.POST.get('course')
            
            if employee_id and course_id:
                try:
                    employee = User.objects.get(id=employee_id)
                    course = Course.objects.get(id=course_id)
                    
                    # Проверяем, существует ли уже такое назначение
                    if not Enrollment.objects.filter(user=employee, course=course).exists():
                        enrollment = Enrollment.objects.create(
                            user=employee, 
                            course=course
                        )
                        
                        # Добавляем запись в журнал активностей
                        ActivityLog.objects.create(
                            user=employee,
                            course=course,
                            action='запись',
                            details=f"HR-менеджер {request.user.username} назначил курс"
                        )
                        
                        messages.success(request, f'Курс "{course.title}" успешно назначен сотруднику {employee.username}.')
                    else:
                        messages.warning(request, 'Этот курс уже назначен данному сотруднику.')
                except (User.DoesNotExist, Course.DoesNotExist):
                    messages.error(request, 'Сотрудник или курс не найден.')
    
    # Автоматическое обновление статусов курсов на основе прогресса
    enrollments = Enrollment.objects.all().select_related('user', 'course')
    for enrollment in enrollments:
        if enrollment.status != 'завершён':
            total_lectures = Lecture.objects.filter(course=enrollment.course).count()
            if total_lectures > 0:
                completed_lectures = CompletedLecture.objects.filter(
                    user=enrollment.user, 
                    lecture__course=enrollment.course
                ).count()
                
                if total_lectures == completed_lectures:
                    old_status = enrollment.status
                    enrollment.status = 'завершён'
                    enrollment.save()
                    
                    # Добавляем запись в журнал активностей
                    ActivityLog.objects.create(
                        user=enrollment.user,
                        course=enrollment.course,
                        action='завершение',
                        details=f"Автоматическое обновление статуса с '{old_status}' на 'завершён'"
                    )
    
    # Получаем обновленные списки
    enrollments = Enrollment.objects.all().select_related('user', 'course')
    recent_activities = ActivityLog.objects.all().order_by('-log_time')[:10]
    
    context = {
        'employees': employees,
        'courses': courses,
        'enrollments': enrollments,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'hr/assign_courses.html', context)

@login_required
def test_difficulty(request):
    if request.user.profile.role != 'training_manager':
        return redirect('home')
    return render(request, 'training_manager/test_difficulty.html')

@login_required
@role_required('admin')
def download_backup(request):
    """Создает и отправляет резервную копию базы данных"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
    
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_dir = tempfile.mkdtemp()
    backup_path = os.path.join(temp_dir, f'backup_{timestamp}.sqlite3')
    
    try:
        shutil.copy2(db_path, backup_path)
        
        response = FileResponse(
            open(backup_path, 'rb'),
            as_attachment=True,
            filename=f'backup_{timestamp}.sqlite3'
        )
        return response
    finally:
        try:
            os.remove(backup_path)
            os.rmdir(temp_dir)
        except:
            pass

class RestoreBackupForm(Form):
    """Форма для загрузки файла бэкапа"""
    backup_file = FileField(label='Файл бэкапа')

@login_required
@role_required('admin')
def restore_backup(request):
    """Восстанавливает базу данных из загруженного бэкапа"""
    if request.method == 'POST':
        form = RestoreBackupForm(request.POST, request.FILES)
        if form.is_valid():
            backup_file = request.FILES['backup_file']
            
            if not backup_file.name.endswith('.sqlite3'):
                messages.error(request, 'Неверный формат файла. Пожалуйста, загрузите файл .sqlite3')
                return redirect('admin_dashboard')
            
            temp_dir = tempfile.mkdtemp()
            temp_path = os.path.join(temp_dir, 'temp_backup.sqlite3')
            
            try:
                with open(temp_path, 'wb+') as destination:
                    for chunk in backup_file.chunks():
                        destination.write(chunk)
                
                try:
                    conn = sqlite3.connect(temp_path)
                    conn.close()
                except sqlite3.Error:
                    messages.error(request, 'Загруженный файл не является корректной базой данных SQLite')
                    return redirect('admin_dashboard')
                
                db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3')
                
                backup_timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                current_backup = f"{db_path}.backup_{backup_timestamp}"
                shutil.copy2(db_path, current_backup)
                
                shutil.copy2(temp_path, db_path)
                
                messages.success(request, 'База данных успешно восстановлена из бэкапа')
                
            except Exception as e:
                messages.error(request, f'Ошибка при восстановлении базы данных: {str(e)}')
            finally:
                try:
                    os.remove(temp_path)
                    os.rmdir(temp_dir)
                except:
                    pass
                    
            return redirect('admin_dashboard')
    else:
        form = RestoreBackupForm()
    
    return render(request, 'admin_panel/restore_backup.html', {'form': form})

@login_required
@role_required('employee')
def my_requests(request):
    training_requests = TrainingRequest.objects.filter(user=request.user).select_related('course').order_by('-created_at')
    return render(request, 'employee/my_requests.html', {'requests': training_requests})

@login_required
@role_required('hr')
def hr_view_requests(request):
    """Позволяет HR-менеджеру просматривать все заявки сотрудников на обучение."""
    
    training_requests = TrainingRequest.objects.all().select_related('user', 'course').order_by('-created_at')
    
    # Обработка фильтрации и поиска
    status_filter = request.GET.get('status', None)
    search_query = request.GET.get('search', None)
    
    if status_filter and status_filter != 'all':
        training_requests = training_requests.filter(status=status_filter)
    
    if search_query:
        training_requests = training_requests.filter(
            Q(user__username__icontains=search_query) | 
            Q(user__first_name__icontains=search_query) | 
            Q(user__last_name__icontains=search_query) |
            Q(course__title__icontains=search_query)
        )
    
    # Возможность действий с заявками
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')

        training_request = get_object_or_404(TrainingRequest, id=request_id)

        if action == 'approve':
            training_request.status = 'approved'
            # При одобрении заявки автоматически создаем запись о зачислении
            Enrollment.objects.get_or_create(
                user=training_request.user,
                course=training_request.course
            )
            messages.success(request, f"Заявка одобрена! Пользователь зачислен на курс '{training_request.course.title}'")
        elif action == 'reject':
            training_request.status = 'rejected'
            messages.info(request, f"Заявка отклонена!")

        training_request.save()
        return redirect('hr_view_requests')
    
    return render(request, 'hr/view_requests.html', {
        'requests': training_requests,
        'current_status': status_filter or 'all',
        'search_query': search_query or ''
    })

@login_required
@role_required('hr')
def manage_employees(request):
    """Страница управления сотрудниками для HR-менеджера"""
    User = get_user_model()
    employees = User.objects.filter(profile__role='employee').select_related('profile')
    
    # Получаем статистику по каждому сотруднику
    employees_data = []
    for employee in employees:
        # Количество назначенных курсов
        assigned_courses = Enrollment.objects.filter(user=employee).count()
        
        # Количество завершенных курсов
        completed_courses = Enrollment.objects.filter(user=employee, status='завершён').count()
        
        # Средний прогресс по всем курсам
        enrollments = Enrollment.objects.filter(user=employee)
        total_progress = 0
        for enrollment in enrollments:
            total_lectures = Lecture.objects.filter(course=enrollment.course).count()
            if total_lectures > 0:
                completed_lectures = CompletedLecture.objects.filter(
                    user=employee, 
                    lecture__course=enrollment.course
                ).count()
                progress = (completed_lectures / total_lectures) * 100
                total_progress += progress
        
        avg_progress = total_progress / assigned_courses if assigned_courses > 0 else 0
        
        # Средний балл по тестам
        test_attempts = TestAttempt.objects.filter(user=employee)
        avg_score = test_attempts.aggregate(Avg('score'))['score__avg'] or 0
        
        employees_data.append({
            'employee': employee,
            'assigned_courses': assigned_courses,
            'completed_courses': completed_courses,
            'avg_progress': round(avg_progress, 1),
            'avg_score': round(avg_score, 1)
        })
    
    context = {
        'employees_data': employees_data
    }
    
    return render(request, 'hr/manage_employees.html', context)

@login_required
def user_guide(request):
    # Check if user is an employee
    if request.user.profile.role != 'employee':
        return redirect('dashboard_redirect')
        
    guide = UserGuide.objects.first()  # Получаем первое руководство
    if not guide:
        # Создаем руководство по умолчанию
        guide = UserGuide.objects.create(
            title="Добро пожаловать в BustCom!",
            content="""
            <h2>Руководство по использованию платформы</h2>
            <p>Добро пожаловать в BustCom - вашу платформу для обучения и развития!</p>
            
            <h3>1. Начало работы</h3>
            <p>После регистрации вам будет предложено пройти небольшой тест, который поможет определить ваши интересы и уровень знаний. На основе результатов теста система подберет для вас наиболее подходящие курсы.</p>
            
            <h3>2. Навигация по платформе</h3>
            <p>В верхней части экрана находится главное меню, где вы можете:</p>
            <ul>
                <li>Перейти на главную страницу</li>
                <li>Просмотреть доступные курсы</li>
                <li>Открыть личный кабинет</li>
                <li>Выйти из системы</li>
            </ul>
            
            <h3>3. Работа с курсами</h3>
            <p>На странице курсов вы увидите три вкладки:</p>
            <ul>
                <li><strong>Рекомендованные</strong> - курсы, подобранные специально для вас</li>
                <li><strong>Все курсы</strong> - полный каталог доступных курсов</li>
                <li><strong>Мои курсы</strong> - курсы, на которые вы записаны</li>
            </ul>
            
            <h3>4. Прохождение курса</h3>
            <p>Каждый курс состоит из:</p>
            <ul>
                <li>Лекций с теоретическим материалом</li>
                <li>Практических заданий</li>
                <li>Тестов для проверки знаний</li>
            </ul>
            
            <h3>5. Сертификация</h3>
            <p>После успешного прохождения курса вы получите сертификат, подтверждающий ваши знания.</p>
            
            <h3>6. Поддержка</h3>
            <p>Если у вас возникнут вопросы, вы всегда можете обратиться к преподавателю курса или в службу поддержки.</p>
            """
        )
    
    # Проверяем, прошел ли пользователь руководство
    guide_progress, created = UserGuideProgress.objects.get_or_create(
        user=request.user,
        guide=guide
    )
    
    if request.method == 'POST':
        guide_progress.completed = True
        guide_progress.completed_at = timezone.now()
        guide_progress.save()
        return redirect('recommendation_test')
    
    return render(request, 'bustComProj/user_guide.html', {'guide': guide})

@login_required
def recommendation_test(request):
    # Check if user is an employee
    if request.user.profile.role != 'employee':
        return redirect('dashboard_redirect')
        
    # Проверяем, прошел ли пользователь тест
    if UserRecommendationTestResult.objects.filter(user=request.user).exists():
        return redirect('courses_list')
    
    questions = RecommendationTest.objects.all()
    if not questions.exists():
        # Создаем тест по умолчанию
        questions = [
            RecommendationTest.objects.create(
                question="Какой тип задач вам больше нравится?",
                options=json.dumps({
                    "a": "Аналитические и логические",
                    "b": "Творческие и креативные",
                    "c": "Коммуникативные и социальные",
                    "d": "Технические и практические"
                }),
                correct_answer="a",
                skill_category="general"
            ),
            RecommendationTest.objects.create(
                question="Какой уровень программирования у вас?",
                options=json.dumps({
                    "a": "Начинающий",
                    "b": "Средний",
                    "c": "Продвинутый",
                    "d": "Нет опыта"
                }),
                correct_answer="a",
                skill_category="programming"
            ),
            # Добавьте больше вопросов по необходимости
        ]
    
    if request.method == 'POST':
        try:
            for question in questions:
                answer = request.POST.get(f'question_{question.id}')
                if not answer:
                    messages.error(request, 'Пожалуйста, ответьте на все вопросы.')
                    return render(request, 'bustComProj/recommendation_test.html', {'questions': questions})
                
                UserRecommendationTestResult.objects.create(
                    user=request.user,
                    test=question,
                    answer=answer,
                    is_correct=answer == question.correct_answer
                )
            # Mark guide as seen after completing the test
            profile = request.user.profile
            profile.has_seen_guide = True
            profile.save()
            return redirect('courses_list')
        except Exception as e:
            messages.error(request, 'Произошла ошибка при сохранении ответов. Пожалуйста, попробуйте снова.')
            return render(request, 'bustComProj/recommendation_test.html', {'questions': questions})
    
    # Преобразуем options из JSON в словарь для каждого вопроса
    for question in questions:
        question.options = json.loads(question.options)
    
    return render(request, 'bustComProj/recommendation_test.html', {'questions': questions})

@login_required
def first_login_guide(request):
    if request.method == 'POST':
        return redirect('recommendation_test')
    return render(request, 'bustComProj/first_login_guide.html')

@login_required
@role_required('teacher')
def teacher_statistics(request):
    """View for teacher to see statistics about their students' performance"""
    # Get courses taught by this teacher
    teacher_courses = Course.objects.filter(teacher=request.user)
    
    courses_statistics = []
    for course in teacher_courses:
        # Get all enrollments for this course
        enrollments = Enrollment.objects.filter(course=course)
        
        # Calculate course statistics
        total_students = enrollments.count()
        completed_count = enrollments.filter(status='завершён').count()
        
        # Calculate average progress
        total_lectures = Lecture.objects.filter(course=course).count()
        course_progress = []
        
        for enrollment in enrollments:
            completed_lectures = CompletedLecture.objects.filter(
                user=enrollment.user,
                lecture__course=course
            ).count()
            if total_lectures > 0:
                progress = (completed_lectures / total_lectures) * 100
                course_progress.append(progress)
        
        avg_progress = sum(course_progress) / len(course_progress) if course_progress else 0
        
        # Get test statistics
        course_tests = Test.objects.filter(lecture__course=course)
        test_attempts = TestAttempt.objects.filter(test__in=course_tests)
        
        avg_test_score = test_attempts.aggregate(Avg('score'))['score__avg'] or 0
        max_test_score = test_attempts.aggregate(Max('score'))['score__max'] or 0
        min_test_score = test_attempts.aggregate(Min('score'))['score__min'] or 0
        
        courses_statistics.append({
            'course': course,
            'total_students': total_students,
            'completed_count': completed_count,
            'avg_progress': round(avg_progress, 1),
            'avg_test_score': round(avg_test_score, 1),
            'max_test_score': max_test_score,
            'min_test_score': min_test_score,
            'total_lectures': total_lectures
        })
    
    return render(request, 'bustComProj/teacher_statistics.html', {
        'courses_statistics': courses_statistics
    })
