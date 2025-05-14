import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bustCom.settings')
django.setup()

from bustComProj.models import (
    User, Course, Lecture, Test, Question, Answer, 
    Enrollment, Progress, Certificate, Notification,
    TrainingPlan, Profile
)
from django.utils import timezone

def create_users():
    # Создаем преподавателей
    teachers = []
    teacher_data = [
        {'username': 'ivanov_teacher', 'email': 'ivanov@example.com', 'first_name': 'Иван', 'last_name': 'Иванов'},
        {'username': 'petrova_teacher', 'email': 'petrova@example.com', 'first_name': 'Мария', 'last_name': 'Петрова'},
        {'username': 'sidorov_teacher', 'email': 'sidorov@example.com', 'first_name': 'Петр', 'last_name': 'Сидоров'},
    ]
    
    for data in teacher_data:
        teacher = User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password='teacher123',
            first_name=data['first_name'],
            last_name=data['last_name'],
            role='teacher'
        )
        Profile.objects.create(
            user=teacher,
            role='teacher',
            phone=f'+7900{random.randint(1000000, 9999999)}',
            company='BustCom Academy'
        )
        teachers.append(teacher)

    # Создаем сотрудников
    employees = []
    for i in range(20):
        username = f'employee_{i}'
        employee = User.objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='employee123',
            first_name=f'Сотрудник_{i}',
            last_name=f'Фамилия_{i}',
            role='employee'
        )
        Profile.objects.create(
            user=employee,
            role='employee',
            phone=f'+7911{random.randint(1000000, 9999999)}',
            company='BustCom Corp'
        )
        employees.append(employee)

    return teachers, employees

def create_courses(teachers):
    courses = []
    course_data = [
        {
            'title': 'Python для начинающих',
            'description': 'Базовый курс по программированию на Python. Изучение основных конструкций языка, работа с данными, функции и классы.',
            'duration': 40,
            'level': 'beginner'
        },
        {
            'title': 'Продвинутый JavaScript',
            'description': 'Углубленное изучение JavaScript, включая асинхронное программирование, работу с DOM, современные фреймворки.',
            'duration': 60,
            'level': 'advanced'
        },
        {
            'title': 'Основы SQL',
            'description': 'Изучение основ работы с базами данных, написание запросов, управление данными.',
            'duration': 30,
            'level': 'beginner'
        },
        {
            'title': 'DevOps практики',
            'description': 'Изучение современных практик DevOps, работа с контейнерами, CI/CD, мониторинг.',
            'duration': 50,
            'level': 'intermediate'
        },
        {
            'title': 'Управление проектами',
            'description': 'Методологии управления проектами, работа с командой, планирование и контроль.',
            'duration': 45,
            'level': 'intermediate'
        }
    ]

    for data in course_data:
        course = Course.objects.create(
            title=data['title'],
            description=data['description'],
            duration=data['duration'],
            level=data['level'],
            teacher=random.choice(teachers)
        )
        courses.append(course)

    return courses

def create_lectures(courses):
    lectures = []
    for course in courses:
        num_lectures = random.randint(5, 10)
        for i in range(num_lectures):
            lecture = Lecture.objects.create(
                course=course,
                title=f'Лекция {i+1}: {random.choice(["Введение", "Основы", "Практика", "Теория", "Закрепление"])}',
                order_num=i+1
            )
            lectures.append(lecture)
    return lectures

def create_tests(lectures):
    tests = []
    difficulties = ['низкая', 'средняя', 'высокая']
    
    for lecture in lectures:
        test = Test.objects.create(
            lecture=lecture,
            name=f'Тест по теме: {lecture.title}',
            difficulty=random.choice(difficulties),
            attempts=3
        )
        
        # Создаем вопросы для теста
        num_questions = random.randint(3, 7)
        for i in range(num_questions):
            question = Question.objects.create(
                test=test,
                question_text=f'Вопрос {i+1} по теме {lecture.title}',
                question_type=random.choice(['один', 'несколько', 'ввод'])
            )
            
            # Создаем варианты ответов
            num_answers = random.randint(2, 4)
            correct_answer_set = False
            for j in range(num_answers):
                is_correct = not correct_answer_set and j == num_answers - 1
                if not correct_answer_set and random.random() < 0.3:
                    is_correct = True
                    correct_answer_set = True
                    
                Answer.objects.create(
                    question=question,
                    answer_text=f'Вариант ответа {j+1}',
                    is_correct=is_correct
                )
        
        tests.append(test)
    return tests

def create_enrollments_and_progress(employees, courses, lectures):
    for employee in employees:
        # Записываем сотрудника на случайные курсы
        num_courses = random.randint(1, 3)
        selected_courses = random.sample(courses, num_courses)
        
        for course in selected_courses:
            # Создаем запись на курс
            enrollment = Enrollment.objects.create(
                user=employee,
                course=course,
                status=random.choice(['в процессе', 'завершён', 'отчислен'])
            )
            
            # Создаем прогресс по лекциям
            course_lectures = Lecture.objects.filter(course=course)
            for lecture in course_lectures:
                if random.random() < 0.7:  # 70% шанс завершения лекции
                    Progress.objects.create(
                        user=employee,
                        course=course,
                        lecture=lecture,
                        completed_at=timezone.now() - timedelta(days=random.randint(1, 30))
                    )

def create_certificates(employees, courses):
    grades = ['A', 'B', 'C', 'A+', 'B+']
    for employee in employees:
        # Выдаем сертификаты за некоторые завершенные курсы
        completed_enrollments = Enrollment.objects.filter(
            user=employee,
            status='завершён'
        )
        
        for enrollment in completed_enrollments:
            if random.random() < 0.8:  # 80% шанс получения сертификата
                Certificate.objects.create(
                    user=employee,
                    course=enrollment.course,
                    grade=random.choice(grades)
                )

def create_training_plans(courses, employees):
    plan_titles = [
        'План обучения разработчиков',
        'Повышение квалификации менеджеров',
        'Обучение новых сотрудников',
        'Программа развития soft skills',
        'Техническое обучение'
    ]
    
    for title in plan_titles:
        plan = TrainingPlan.objects.create(
            title=title,
            description=f'План обучения: {title}',
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=90)).date(),
            status=random.choice(['draft', 'active', 'completed']),
            created_by=random.choice(employees)
        )
        
        # Добавляем случайные курсы в план
        num_courses = random.randint(2, 4)
        selected_courses = random.sample(list(courses), num_courses)
        plan.courses.set(selected_courses)
        
        # Назначаем случайных сотрудников
        num_employees = random.randint(3, 8)
        selected_employees = random.sample(employees, num_employees)
        plan.employees.set(selected_employees)

def create_notifications(users):
    notification_templates = [
        'Новый курс доступен: {}',
        'Напоминание о дедлайне по курсу {}',
        'Поздравляем с завершением курса {}',
        'Новый тест доступен в курсе {}',
        'Обновление материалов в курсе {}'
    ]
    
    courses = Course.objects.all()
    for user in users:
        num_notifications = random.randint(2, 5)
        for _ in range(num_notifications):
            course = random.choice(courses)
            template = random.choice(notification_templates)
            Notification.objects.create(
                user=user,
                message=template.format(course.title),
                status=random.choice(['новое', 'прочитано'])
            )

def main():
    # Очищаем существующие данные
    print("Очистка существующих данных...")
    Profile.objects.all().delete()
    User.objects.exclude(is_superuser=True).delete()
    Course.objects.all().delete()
    
    print("Создание пользователей...")
    teachers, employees = create_users()
    
    print("Создание курсов...")
    courses = create_courses(teachers)
    
    print("Создание лекций...")
    lectures = create_lectures(courses)
    
    print("Создание тестов...")
    tests = create_tests(lectures)
    
    print("Создание записей на курсы и прогресса...")
    create_enrollments_and_progress(employees, courses, lectures)
    
    print("Создание сертификатов...")
    create_certificates(employees, courses)
    
    print("Создание планов обучения...")
    create_training_plans(courses, employees)
    
    print("Создание уведомлений...")
    create_notifications(employees + teachers)
    
    print("База данных успешно наполнена тестовыми данными!")

if __name__ == '__main__':
    main() 