import os
import django
import random
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bustCom.settings')
django.setup()

from bustComProj.models import User, Course, Lecture, Test, Question, Answer
from django.utils import timezone

def ensure_teacher_exists():
    # Проверяем существование учителя или создаем нового
    teacher = User.objects.filter(role='teacher').first()
    if not teacher:
        teacher = User.objects.create_user(
            username='default_teacher',
            email='teacher@example.com',
            password='teacher123',
            first_name='Преподаватель',
            last_name='Системный',
            role='teacher'
        )
    return teacher

def ensure_courses_exist():
    # Проверяем существование курсов
    if Course.objects.count() == 0:
        teacher = ensure_teacher_exists()
        
        course_data = [
            {
                'title': 'Разработка веб-приложений',
                'description': 'Полный курс по созданию современных веб-приложений, включая фронтенд и бэкенд разработку.',
                'duration': 60,
                'level': 'intermediate'
            },
            {
                'title': 'Основы программирования',
                'description': 'Базовый курс программирования для начинающих. Алгоритмы, структуры данных, основы ООП.',
                'duration': 40,
                'level': 'beginner'
            },
            {
                'title': 'Управление проектами в IT',
                'description': 'Методологии управления проектами, работа с командой, планирование и контроль в IT-сфере.',
                'duration': 45,
                'level': 'intermediate'
            },
            {
                'title': 'Безопасность информационных систем',
                'description': 'Курс по информационной безопасности, включающий защиту данных, сетевую безопасность и криптографию.',
                'duration': 50,
                'level': 'advanced'
            },
            {
                'title': 'Машинное обучение и AI',
                'description': 'Введение в машинное обучение и искусственный интеллект. Основные алгоритмы и их применение.',
                'duration': 55,
                'level': 'advanced'
            }
        ]
        
        print("Создание базовых курсов...")
        for data in course_data:
            Course.objects.create(
                title=data['title'],
                description=data['description'],
                duration=data['duration'],
                level=data['level'],
                teacher=teacher
            )
            print(f"Создан курс: {data['title']}")

def add_lectures_and_tests():
    # Убеждаемся, что курсы существуют
    ensure_courses_exist()
    
    # Получаем все существующие курсы
    courses = Course.objects.all()
    
    lecture_themes = [
        "Введение в тему",
        "Основные концепции",
        "Практическое применение",
        "Углубленное изучение",
        "Работа с инструментами",
        "Лучшие практики",
        "Решение проблем",
        "Оптимизация процессов",
        "Современные подходы",
        "Разбор кейсов",
        "Командная работа",
        "Методология разработки",
        "Архитектурные решения",
        "Безопасность и защита",
        "Масштабирование систем"
    ]
    
    subtopics = [
        "Базовые принципы",
        "Продвинутые техники",
        "Практические примеры",
        "Типовые решения",
        "Инструменты и фреймворки",
        "Методы оптимизации",
        "Стратегии внедрения",
        "Анализ производительности",
        "Управление ресурсами",
        "Интеграция систем"
    ]

    print(f"Найдено курсов: {len(courses)}")
    
    for course in courses:
        print(f"\nДобавление контента для курса: {course.title}")
        
        # Добавляем новые лекции
        existing_lectures = Lecture.objects.filter(course=course).count()
        new_lectures_count = random.randint(8, 15)
        
        for i in range(new_lectures_count):
            theme = random.choice(lecture_themes)
            subtopic = random.choice(subtopics)
            
            lecture = Lecture.objects.create(
                course=course,
                title=f"{theme}: {subtopic}",
                order_num=existing_lectures + i + 1
            )
            print(f"Создана лекция: {lecture.title}")
            
            # Создаем тест для лекции
            test = Test.objects.create(
                lecture=lecture,
                name=f"Тест по теме: {lecture.title}",
                difficulty=random.choice(['низкая', 'средняя', 'высокая']),
                attempts=3
            )
            
            # Создаем вопросы для теста
            question_templates = [
                "Какие основные принципы используются в {}?",
                "Как правильно применять {} на практике?",
                "В чем преимущества использования {} перед альтернативными подходами?",
                "Какие проблемы решает {}?",
                "Опишите процесс внедрения {} в существующую систему.",
                "Какие инструменты используются при работе с {}?",
                "Как обеспечить безопасность при использовании {}?",
                "Назовите основные компоненты {}.",
                "Какие лучшие практики существуют для работы с {}?",
                "Как оптимизировать производительность при использовании {}?"
            ]
            
            num_questions = random.randint(5, 10)
            for j in range(num_questions):
                question_text = random.choice(question_templates).format(subtopic)
                question = Question.objects.create(
                    test=test,
                    question_text=question_text,
                    question_type=random.choice(['один', 'несколько', 'ввод'])
                )
                
                # Создаем варианты ответов
                answer_templates = [
                    "Использовать стандартные методы",
                    "Применить специализированные инструменты",
                    "Следовать лучшим практикам отрасли",
                    "Разработать собственное решение",
                    "Использовать готовые фреймворки",
                    "Провести анализ требований",
                    "Внедрить систему мониторинга",
                    "Оптимизировать существующие процессы"
                ]
                
                num_answers = random.randint(3, 5)
                correct_answer_set = False
                
                for k in range(num_answers):
                    answer_text = f"{random.choice(answer_templates)} для {subtopic}"
                    is_correct = not correct_answer_set and (k == num_answers - 1 or random.random() < 0.3)
                    
                    if is_correct:
                        correct_answer_set = True
                    
                    Answer.objects.create(
                        question=question,
                        answer_text=answer_text,
                        is_correct=is_correct
                    )
            
            print(f"Создан тест с {num_questions} вопросами")

if __name__ == '__main__':
    print("Начало добавления лекций и тестов...")
    add_lectures_and_tests()
    print("\nГотово! Лекции и тесты успешно добавлены.") 