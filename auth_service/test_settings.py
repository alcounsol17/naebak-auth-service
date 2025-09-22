"""
إعدادات خاصة للاختبارات
"""
from .settings import *

# إزالة django_ratelimit من INSTALLED_APPS للاختبارات
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != 'django_ratelimit']

# إزالة middleware الخاص بـ rate limiting
MIDDLEWARE = [
    middleware for middleware in MIDDLEWARE 
    if 'LoginAttemptMiddleware' not in middleware
]

# تعطيل cache للاختبارات
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# استخدام SQLite للاختبارات
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}



# تعطيل التسجيل أثناء الاختبارات
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
}

# تعطيل Rate Limiting للاختبارات
RATELIMIT_ENABLE = False

# إعدادات أمان مبسطة للاختبارات
SECRET_KEY = 'test-secret-key-for-testing-only'
JWT_SECRET_KEY = 'test-jwt-secret-key'

# تعطيل Google Secret Manager للاختبارات
USE_SECRET_MANAGER = False
