from pathlib import Path

# 🔹 Базовая конфигурация проекта
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-yc6#faw=i_d9x88z@r$at--5!1+qf72(y)ay=i1b#j!r^6u+o)'
DEBUG = True
ALLOWED_HOSTS = ["*"]

# 🔹 Установленные приложения
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bustComProj',
]

# 🔹 Middleware (посредники)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 🔹 Основной конфиг Django
ROOT_URLCONF = 'bustCom.urls'
WSGI_APPLICATION = 'bustCom.wsgi.application'

# 🔹 Шаблоны
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# 🔹 База данных (SQLite, можно заменить на PostgreSQL/MySQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🔹 Локализация
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# 🔹 Пути для статики
STATIC_URL = 'static/'

# 🔹 Пользовательская модель
AUTH_USER_MODEL = 'bustComProj.User'

# 🔹 Настройки аутентификации и сессий
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
SESSION_COOKIE_AGE = 86400  # 1 день (24 часа)
SESSION_SAVE_EVERY_REQUEST = True  # Продление сессии при каждом запросе

# 🔹 Отключение проверки сложности пароля (пароль может быть 123)
AUTH_PASSWORD_VALIDATORS = []

# 🔹 Автоинкремент для первичных ключей
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
