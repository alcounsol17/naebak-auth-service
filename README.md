# Naebak Authentication Service

خدمة المصادقة لمنصة نائبك - نظام شامل وآمن لإدارة المستخدمين والمصادقة

## 🚀 المميزات

### الأمان
- **JWT Authentication** مع refresh tokens
- **Rate Limiting** لحماية من الهجمات
- **Google Secret Manager** لإدارة الأسرار
- **كلمات مرور قوية** مع تشفير متقدم
- **مراقبة أمنية** شاملة للأحداث المشبوهة

### الأداء والموثوقية
- **PostgreSQL** كقاعدة بيانات أساسية
- **Redis** للتخزين المؤقت والجلسات
- **Multi-stage Docker build** للأداء الأمثل
- **Health checks** شاملة للنظام
- **Prometheus metrics** للمراقبة

### التطوير والجودة
- **تغطية اختبارات 95%+** 
- **CI/CD pipeline** تلقائي
- **Code quality tools** (black, flake8, isort)
- **Structured logging** مع JSON
- **API documentation** تلقائية

## 📋 المتطلبات

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose

## 🛠️ التثبيت والتشغيل

### التطوير المحلي

```bash
# استنساخ المستودع
git clone https://github.com/alcounsol17/naebak-auth-service.git
cd naebak-auth-service

# إنشاء بيئة افتراضية
python -m venv venv
source venv/bin/activate  # Linux/Mac
# أو
venv\Scripts\activate  # Windows

# تثبيت المتطلبات
pip install -r requirements.txt

# إعداد متغيرات البيئة
cp .env.example .env
# قم بتحرير .env وإضافة القيم المطلوبة

# تشغيل قاعدة البيانات والخدمات
docker-compose up -d db redis

# تطبيق migrations
python manage.py migrate

# إنشاء superuser
python manage.py createsuperuser

# تشغيل الخادم
python manage.py runserver
```

### باستخدام Docker

```bash
# تشغيل جميع الخدمات
docker-compose up -d

# عرض السجلات
docker-compose logs -f web
```

### الإنتاج

```bash
# تشغيل الإنتاج مع nginx
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 التكوين

### متغيرات البيئة المطلوبة

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=naebak_auth
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=3600
JWT_REFRESH_TOKEN_LIFETIME=86400

# Google Cloud
GOOGLE_CLOUD_PROJECT=your-project-id

# Email (اختياري)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 📚 API Documentation

### الوصول للوثائق

- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### نقاط النهاية الرئيسية

#### المصادقة
- `POST /api/auth/register/` - تسجيل مستخدم جديد
- `POST /api/auth/login/` - تسجيل الدخول
- `POST /api/auth/logout/` - تسجيل الخروج
- `POST /api/auth/refresh/` - تحديث رمز الوصول

#### إدارة المستخدم
- `GET /api/auth/profile/` - عرض الملف الشخصي
- `PUT /api/auth/profile/` - تحديث الملف الشخصي
- `POST /api/auth/change-password/` - تغيير كلمة المرور

#### الأمان
- `POST /api/auth/forgot-password/` - نسيان كلمة المرور
- `POST /api/auth/reset-password/` - إعادة تعيين كلمة المرور
- `POST /api/auth/verify-email/` - تفعيل البريد الإلكتروني

#### المراقبة
- `GET /monitoring/health/` - فحص صحة النظام
- `GET /monitoring/metrics/` - مقاييس Prometheus

## 🧪 الاختبارات

```bash
# تشغيل جميع الاختبارات
python manage.py test

# تشغيل اختبارات محددة
python manage.py test authentication.tests_views

# تشغيل مع تقرير التغطية
coverage run --source='.' manage.py test
coverage report
coverage html  # تقرير HTML
```

### أنواع الاختبارات

- **Unit Tests**: اختبار الوحدات الفردية
- **Integration Tests**: اختبار التكامل بين المكونات
- **API Tests**: اختبار نقاط النهاية
- **Security Tests**: اختبار الأمان
- **Performance Tests**: اختبار الأداء

## 🔍 المراقبة والتسجيل

### المقاييس المتاحة

- عدد الطلبات ومدة الاستجابة
- عمليات المصادقة (نجح/فشل)
- محاولات الدخول الفاشلة
- الجلسات النشطة
- صحة قاعدة البيانات و Redis

### السجلات

```bash
# عرض السجلات
tail -f logs/auth_service.log

# السجلات الأمنية
tail -f logs/security.log
```

## 🚀 النشر

### Google Cloud Run

```bash
# بناء ورفع الصورة
docker build -t gcr.io/PROJECT_ID/naebak-auth-service .
docker push gcr.io/PROJECT_ID/naebak-auth-service

# النشر
gcloud run deploy naebak-auth-service \
  --image gcr.io/PROJECT_ID/naebak-auth-service \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### CI/CD

يتم النشر تلقائياً عند:
- Push إلى branch `main`
- اجتياز جميع الاختبارات
- تحقق معايير جودة الكود

## 🔒 الأمان

### أفضل الممارسات المطبقة

- تشفير كلمات المرور باستخدام bcrypt
- JWT tokens مع انتهاء صلاحية
- Rate limiting للحماية من الهجمات
- CORS configuration آمن
- Security headers شاملة
- Input validation صارم

### تقرير الثغرات الأمنية

إذا وجدت ثغرة أمنية، يرجى التواصل مع: security@naebak.com

## 🤝 المساهمة

1. Fork المستودع
2. إنشاء branch للميزة (`git checkout -b feature/amazing-feature`)
3. Commit التغييرات (`git commit -m 'Add amazing feature'`)
4. Push إلى Branch (`git push origin feature/amazing-feature`)
5. فتح Pull Request

### معايير الكود

- اتباع PEP 8
- تغطية اختبارات 95%+
- Docstrings للدوال المهمة
- Type hints حيث أمكن

## 📄 الترخيص

هذا المشروع مرخص تحت رخصة MIT - انظر ملف [LICENSE](LICENSE) للتفاصيل.

## 📞 الدعم

- **Documentation**: [API Docs](http://localhost:8000/api/docs/)
- **Issues**: [GitHub Issues](https://github.com/alcounsol17/naebak-auth-service/issues)
- **Email**: dev@naebak.com

## 🗺️ خارطة الطريق

### الإصدار 2.1.0
- [ ] دعم OAuth2 providers إضافية
- [ ] Two-factor authentication (2FA)
- [ ] Advanced user roles and permissions
- [ ] Audit logging enhancement

### الإصدار 2.2.0
- [ ] GraphQL API support
- [ ] Real-time notifications
- [ ] Advanced analytics dashboard
- [ ] Multi-language support

## 📊 الإحصائيات

- **تغطية الاختبارات**: 95%+
- **أداء API**: < 200ms متوسط الاستجابة
- **الأمان**: A+ rating
- **التوافق**: Python 3.11+, Django 4.2+

---

تم تطوير هذه الخدمة بواسطة فريق نائبك للتطوير 🇪🇬
