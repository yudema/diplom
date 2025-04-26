from django.core.management.base import BaseCommand
from django.utils import timezone
from bustComProj.models import Course, Lecture, Test, Question, Answer, User

class Command(BaseCommand):
    help = 'Load initial course data'

    def handle(self, *args, **kwargs):
        try:
            # Create a teacher user if it doesn't exist
            try:
                teacher = User.objects.get(username='teacher1')
                self.stdout.write(self.style.SUCCESS('Teacher user already exists'))
            except User.DoesNotExist:
                teacher = User.objects.create_user(
                    username='teacher1',
                    email='teacher1@example.com',
                    password='teacher123',
                    role='teacher'
                )
                self.stdout.write(self.style.SUCCESS('Teacher user created successfully'))

            # Course data
            courses_data = [
                {
                    'title': 'Основы Python разработки',
                    'description': 'Базовый курс по Python программированию',
                    'duration': 40,
                    'level': 'beginner',
                    'teacher': teacher
                },
                {
                    'title': 'JavaScript для фронтенд-разработчиков',
                    'description': 'Изучение JavaScript и основных концепций фронтенд-разработки',
                    'duration': 50,
                    'level': 'intermediate',
                    'teacher': teacher
                },
                {
                    'title': 'Продвинутая веб-разработка',
                    'description': 'Углубленное изучение веб-технологий',
                    'duration': 60,
                    'level': 'advanced',
                    'teacher': teacher
                },
                {
                    'title': 'SQL и базы данных',
                    'description': 'Основы работы с базами данных, SQL запросы, проектирование схем',
                    'duration': 45,
                    'level': 'beginner',
                    'teacher': teacher
                },
                {
                    'title': 'React для профессионалов',
                    'description': 'Продвинутая разработка на React, паттерны, оптимизация',
                    'duration': 55,
                    'level': 'advanced',
                    'teacher': teacher
                },
                {
                    'title': 'Docker и контейнеризация',
                    'description': 'Работа с Docker, оркестрация контейнеров, микросервисы',
                    'duration': 35,
                    'level': 'intermediate',
                    'teacher': teacher
                },
                {
                    'title': 'Машинное обучение на Python',
                    'description': 'Основы ML, работа с данными, построение моделей',
                    'duration': 70,
                    'level': 'advanced',
                    'teacher': teacher
                },
                {
                    'title': 'Кибербезопасность',
                    'description': 'Основы информационной безопасности, защита приложений',
                    'duration': 50,
                    'level': 'intermediate',
                    'teacher': teacher
                },
                {
                    'title': 'UI/UX Дизайн',
                    'description': 'Принципы дизайна интерфейсов, прототипирование, юзабилити',
                    'duration': 40,
                    'level': 'beginner',
                    'teacher': teacher
                },
                {
                    'title': 'Git для команд',
                    'description': 'Продвинутая работа с Git, командная разработка',
                    'duration': 30,
                    'level': 'intermediate',
                    'teacher': teacher
                },
                {
                    'title': 'Облачные технологии AWS',
                    'description': 'Работа с сервисами AWS, архитектура облачных приложений',
                    'duration': 65,
                    'level': 'advanced',
                    'teacher': teacher
                },
                {
                    'title': 'Agile и Scrum',
                    'description': 'Методологии гибкой разработки, управление проектами',
                    'duration': 35,
                    'level': 'beginner',
                    'teacher': teacher
                },
                {
                    'title': 'Тестирование ПО',
                    'description': 'Автоматизация тестирования, CI/CD, качество кода',
                    'duration': 45,
                    'level': 'intermediate',
                    'teacher': teacher
                }
            ]

            # Create courses
            for course_data in courses_data:
                course, created = Course.objects.get_or_create(
                    title=course_data['title'],
                    defaults={
                        'description': course_data['description'],
                        'duration': course_data['duration'],
                        'level': course_data['level'],
                        'teacher': course_data['teacher']
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f'Course "{course.title}" created successfully'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'Course "{course.title}" already exists'))

                # Add lectures and tests for each course
                lecture1, _ = Lecture.objects.get_or_create(
                    course=course,
                    title=f'Введение в {course.title}',
                    defaults={
                        'order_num': 1
                    }
                )
                
                test, _ = Test.objects.get_or_create(
                    lecture=lecture1,
                    name=f'Вводный тест - {course.title}',
                    defaults={
                        'difficulty': 'низкая',
                        'attempts': 3
                    }
                )
                
                question1, _ = Question.objects.get_or_create(
                    test=test,
                    question_text=f'Что такое {course.title}?',
                    defaults={
                        'question_type': 'один'
                    }
                )
                
                Answer.objects.get_or_create(
                    question=question1,
                    answer_text='Важная технология в современной разработке',
                    is_correct=True
                )

            self.stdout.write(self.style.SUCCESS('All course data loaded successfully'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Failed to load course data: {str(e)}')) 