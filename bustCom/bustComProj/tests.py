from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Course, Lecture, Test, Question, Answer, TestAttempt, Enrollment, Profile
from django.utils import timezone

class CourseTests(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(
            username='testteacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        Profile.objects.filter(user=self.user).delete()
        Profile.objects.create(user=self.user, role='teacher')
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            duration=10,
            level='beginner',
            teacher=self.user
        )

    def test_course_creation(self):
        """Тест создания курса"""
        self.assertEqual(self.course.title, 'Test Course')
        self.assertEqual(self.course.duration, 10)
        self.assertEqual(self.course.level, 'beginner')
        self.assertEqual(self.course.teacher, self.user)

    def test_course_str(self):
        """Тест строкового представления курса"""
        self.assertEqual(str(self.course), 'Test Course')

class LectureTests(TransactionTestCase):
    def setUp(self):
        self.teacher = get_user_model().objects.create_user(
            username='testteacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        Profile.objects.filter(user=self.teacher).delete()
        Profile.objects.create(user=self.teacher, role='teacher')
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            duration=10,
            level='beginner',
            teacher=self.teacher
        )
        self.lecture = Lecture.objects.create(
            course=self.course,
            title='Test Lecture',
            order_num=1
        )

    def test_lecture_creation(self):
        """Тест создания лекции"""
        self.assertEqual(self.lecture.title, 'Test Lecture')
        self.assertEqual(self.lecture.order_num, 1)
        self.assertEqual(self.lecture.course, self.course)

    def test_lecture_str(self):
        """Тест строкового представления лекции"""
        self.assertEqual(str(self.lecture), 'Test Lecture')

class TestTests(TransactionTestCase):
    def setUp(self):
        self.teacher = get_user_model().objects.create_user(
            username='testteacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        Profile.objects.filter(user=self.teacher).delete()
        Profile.objects.create(user=self.teacher, role='teacher')
        
        self.student = get_user_model().objects.create_user(
            username='teststudent',
            email='student@test.com',
            password='testpass123',
            role='employee'
        )
        Profile.objects.filter(user=self.student).delete()
        Profile.objects.create(user=self.student, role='employee')
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            duration=10,
            level='beginner',
            teacher=self.teacher
        )
        self.lecture = Lecture.objects.create(
            course=self.course,
            title='Test Lecture',
            order_num=1
        )
        self.test = Test.objects.create(
            lecture=self.lecture,
            name='Test Quiz',
            difficulty='средняя',
            attempts=3
        )
        self.question = Question.objects.create(
            test=self.test,
            question_text='Test Question',
            question_type='один'
        )
        self.answer = Answer.objects.create(
            question=self.question,
            answer_text='Correct Answer',
            is_correct=True
        )

    def test_test_creation(self):
        """Тест создания теста"""
        self.assertEqual(self.test.name, 'Test Quiz')
        self.assertEqual(self.test.difficulty, 'средняя')
        self.assertEqual(self.test.attempts, 3)

    def test_question_creation(self):
        """Тест создания вопроса"""
        self.assertEqual(self.question.question_text, 'Test Question')
        self.assertEqual(self.question.question_type, 'один')

    def test_answer_creation(self):
        """Тест создания ответа"""
        self.assertEqual(self.answer.answer_text, 'Correct Answer')
        self.assertTrue(self.answer.is_correct)

    def test_test_attempt(self):
        """Тест попытки прохождения теста"""
        attempt = TestAttempt.objects.create(
            user=self.student,
            test=self.test,
            score=1,
            total_questions=1,
            percentage=100.0
        )
        self.assertEqual(attempt.score, 1)
        self.assertEqual(attempt.percentage, 100.0)

class TestViewTests(TransactionTestCase):
    def setUp(self):
        self.client = Client()
        self.teacher = get_user_model().objects.create_user(
            username='testteacher',
            email='teacher@test.com',
            password='testpass123',
            role='teacher'
        )
        Profile.objects.filter(user=self.teacher).delete()
        Profile.objects.create(user=self.teacher, role='teacher')
        
        self.student = get_user_model().objects.create_user(
            username='teststudent',
            email='student@test.com',
            password='testpass123',
            role='employee'
        )
        Profile.objects.filter(user=self.student).delete()
        Profile.objects.create(user=self.student, role='employee')
        
        self.course = Course.objects.create(
            title='Test Course',
            description='Test Description',
            duration=10,
            level='beginner',
            teacher=self.teacher
        )
        self.lecture = Lecture.objects.create(
            course=self.course,
            title='Test Lecture',
            order_num=1
        )
        self.test = Test.objects.create(
            lecture=self.lecture,
            name='Test Quiz',
            difficulty='средняя',
            attempts=3
        )
        # Создаем запись о зачислении студента на курс
        self.enrollment = Enrollment.objects.create(
            user=self.student,
            course=self.course,
            status='в процессе'
        )

    def test_test_access_authenticated(self):
        """Тест доступа к тесту для авторизованного пользователя"""
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('lecture_test', args=[self.test.id]))
        self.assertEqual(response.status_code, 200)

    def test_test_access_unauthenticated(self):
        """Тест доступа к тесту для неавторизованного пользователя"""
        response = self.client.get(reverse('lecture_test', args=[self.test.id]))
        self.assertEqual(response.status_code, 302)  # Редирект на страницу входа

    def test_test_submission(self):
        """Тест отправки ответов на тест"""
        self.client.login(username='teststudent', password='testpass123')
        question = Question.objects.create(
            test=self.test,
            question_text='Test Question',
            question_type='один'
        )
        answer = Answer.objects.create(
            question=question,
            answer_text='Correct Answer',
            is_correct=True
        )
        
        response = self.client.post(reverse('submit_test', args=[self.test.id]), {
            f'question_{question.id}': answer.id
        })
        self.assertEqual(response.status_code, 302)  # Редирект после успешной отправки
        
        # Проверяем, что создана запись о попытке
        self.assertTrue(TestAttempt.objects.filter(
            user=self.student,
            test=self.test
        ).exists())
