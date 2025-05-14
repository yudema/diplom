from django.test import TestCase
from django.contrib.auth import get_user_model
from bustComProj.forms import CustomUserCreationForm, CourseForm
from bustComProj.models import Course

User = get_user_model()

class UserRegistrationTest(TestCase):
    def test_user_creation_form(self):
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Тест',
            'last_name': 'Тестович',
            'role': 'employee',
            'password1': 'secure_password_123',
            'password2': 'secure_password_123'
        }
        
        form = CustomUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Форма не прошла валидацию: {form.errors}")
    
    def test_duplicate_username_registration(self):
        User.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123'
        )
        
        form_data = {
            'username': 'existinguser',  
            'email': 'another@example.com',
            'first_name': 'Другой',
            'last_name': 'Пользователь',
            'role': 'employee',
            'password1': 'password123',
            'password2': 'password123'
        }
        
        form = CustomUserCreationForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        
        self.assertIn('username', form.errors)

class CourseTest(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(
            username='teacher',
            email='teacher@example.com',
            password='password123',
            role='teacher'  
        )
    
    def test_course_creation(self):
        course = Course.objects.create(
            title="Тестовый курс",
            description="Описание тестового курса",
            duration=40,
            level="beginner",
            teacher=self.teacher  
        )
        
        self.assertEqual(course.title, "Тестовый курс")
        self.assertEqual(course.description, "Описание тестового курса")
        self.assertEqual(course.duration, 40)
        self.assertEqual(course.level, "beginner")
        self.assertEqual(course.teacher, self.teacher)
    
    def test_course_form_validation(self):
        form_data = {
            'title': 'Новый курс',
            'description': 'Описание нового курса',
            'duration': 25,
            'level': 'intermediate'
        }
        form = CourseForm(data=form_data)
        self.assertTrue(form.is_valid(), f"Форма не прошла валидацию: {form.errors}")