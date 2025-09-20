# خدمة المصادقة - منصة نائبك.كوم
# Naebak Authentication Service

خدمة المصادقة الآمنة لمنصة نائبك.كوم باستخدام JWT وDjango REST Framework.

## المميزات الرئيسية

- 🔐 **مصادقة آمنة**: نظام JWT مع Access و Refresh Tokens
- 👥 **أنواع مستخدمين متعددة**: مواطن، نائب، مشرف
- 📱 **تسجيل شامل**: تتبع عمليات تسجيل الدخول والخروج
- 🛡️ **حماية متقدمة**: تشفير كلمات المرور وحماية من الهجمات
- 🌍 **دعم عربي كامل**: واجهات وقواعد بيانات باللغة العربية

## APIs المتاحة

### المصادقة
- `POST /api/auth/register/` - تسجيل مستخدم جديد
- `POST /api/auth/login/` - تسجيل الدخول
- `POST /api/auth/logout/` - تسجيل الخروج
- `POST /api/auth/refresh-token/` - تحديث الرمز المميز

### الملف الشخصي
- `GET /api/auth/profile/` - عرض الملف الشخصي
- `PUT /api/auth/profile/` - تحديث الملف الشخصي
- `GET /api/auth/user-info/` - معلومات المستخدم الحالي
- `POST /api/auth/change-password/` - تغيير كلمة المرور

### المراقبة
- `GET /api/auth/login-history/` - سجل تسجيل الدخول
- `GET /api/auth/health/` - فحص صحة الخدمة

## التشغيل المحلي

```bash
# إنشاء البيئة الافتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# تثبيت المتطلبات
pip install -r requirements.txt

# إعداد قاعدة البيانات
python manage.py migrate

# إنشاء مستخدم مشرف
python manage.py createsuperuser

# تشغيل الخادم
python manage.py runserver
```

## النشر باستخدام Docker

```bash
# بناء الصورة
docker build -t naebak-auth-service .

# تشغيل الحاوية
docker run -p 8000:8000 naebak-auth-service
```

## متغيرات البيئة

```env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
ALLOWED_HOSTS=your-domain.com
CORS_ALLOWED_ORIGINS=https://your-frontend.com
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=86400
```

## هيكل المشروع

```
naebak-auth-service/
├── auth_service/          # إعدادات Django الرئيسية
├── authentication/        # تطبيق المصادقة
│   ├── models.py         # نماذج قاعدة البيانات
│   ├── views.py          # واجهات API
│   ├── serializers.py    # مسلسلات البيانات
│   ├── authentication.py # نظام JWT
│   └── urls.py          # مسارات API
├── requirements.txt      # متطلبات Python
├── Dockerfile           # ملف Docker
└── README.md           # هذا الملف
```

## الأمان

- كلمات المرور مشفرة باستخدام Django's PBKDF2
- رموز JWT موقعة ومؤمنة
- حماية من CORS attacks
- تسجيل شامل لعمليات الأمان
- التحقق من صحة البيانات المدخلة

## المساهمة

هذا المشروع جزء من منصة نائبك.كوم. للمساهمة:

1. Fork المستودع
2. إنشاء branch جديد للميزة
3. Commit التغييرات
4. Push إلى Branch
5. إنشاء Pull Request

## الترخيص

هذا المشروع مرخص تحت رخصة MIT.

## التواصل

- المطور: alcounsol17
- GitHub: https://github.com/alcounsol17/naebak-auth-service
- المنصة الرئيسية: نائبك.كوم
