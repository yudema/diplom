from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import User, Role, Profile, Course, Comment,Lecture, Test, Question, Answer
from django.forms.widgets import DateInput
User = get_user_model()  

class CustomUserCreationForm(UserCreationForm):
    role = forms.ModelChoiceField(queryset=Role.objects.all(), required=True, label="Роль")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']

        if commit:
            user.save()
            # Create profile with default values
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'role': user.role.name,
                    'has_seen_guide': False
                }
            )
        return user

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description', 'duration', 'level']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название курса'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите описание курса',
                'rows': 4
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Продолжительность в часах'
            }),
            'level': forms.Select(attrs={
                'class': 'form-control'
            })
        }
        labels = {
            'title': 'Название курса',
            'description': 'Описание',
            'duration': 'Продолжительность (часов)',
            'level': 'Уровень сложности'
        }
        help_texts = {
            'duration': 'Укажите примерную продолжительность курса в часах',
            'level': 'Выберите уровень сложности курса'
        }

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, label='Имя')
    last_name = forms.CharField(max_length=30, required=False, label='Фамилия')
    
    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'phone', 'company']
        
    def __init__(self, *args, **kwargs):
        # Получаем пользователя из kwargs, чтобы проверить его роль
        self.user = kwargs.pop('user', None)
        super(ProfileForm, self).__init__(*args, **kwargs)
        
        # Инициализируем поля имени и фамилии данными пользователя
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            
        # Если пользователь не админ, убираем поле роли из формы полностью
        if self.user and not self.user.profile.role == 'admin':
            if 'role' in self.fields:
                del self.fields['role']
            
    def save(self, commit=True):
        profile = super(ProfileForm, self).save(commit=False)
        
        # Обновляем имя и фамилию пользователя
        if hasattr(profile, 'user') and profile.user:
            profile.user.first_name = self.cleaned_data['first_name']
            profile.user.last_name = self.cleaned_data['last_name']
            if commit:
                profile.user.save()
                
        if commit:
            profile.save()
            
        return profile

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']




class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ['title', 'order_num']


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = ['name', 'difficulty', 'attempts']




class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['test', 'question_text', 'question_type']

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['question', 'answer_text', 'is_correct']

