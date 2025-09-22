from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import uuid


class User(AbstractUser):
    """
    نموذج المستخدم المخصص لمنصة نائبك.كوم
    """
    USER_TYPES = (
        ('citizen', 'مواطن'),
        ('representative', 'نائب'),
        ('admin', 'مشرف'),
    )
    
    email = models.EmailField(unique=True, verbose_name='البريد الإلكتروني')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='رقم الهاتف')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='citizen', verbose_name='نوع المستخدم')
    national_id = models.CharField(max_length=14, unique=True, blank=True, null=True, verbose_name='الرقم القومي')
    governorate = models.CharField(max_length=50, blank=True, null=True, verbose_name='المحافظة')
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name='المدينة')
    address = models.TextField(blank=True, null=True, verbose_name='العنوان')
    birth_date = models.DateField(blank=True, null=True, verbose_name='تاريخ الميلاد')
    profile_picture = models.URLField(blank=True, null=True, verbose_name='صورة الملف الشخصي')
    is_verified = models.BooleanField(default=False, verbose_name='تم التحقق')
    verification_token = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, verbose_name='تاريخ الإنشاء')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاريخ التحديث')
    last_login_ip = models.GenericIPAddressField(blank=True, null=True, verbose_name='آخر IP للدخول')
    
    # Google OAuth fields
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name='معرف Google')
    google_email = models.EmailField(blank=True, null=True, verbose_name='بريد Google الإلكتروني')
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'
        db_table = 'auth_users'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def is_citizen(self):
        return self.user_type == 'citizen'
    
    def is_representative(self):
        return self.user_type == 'representative'
    
    def is_admin_user(self):
        return self.user_type == 'admin'


class RefreshToken(models.Model):
    """
    نموذج رموز التحديث (Refresh Tokens)
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refresh_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'رمز التحديث'
        verbose_name_plural = 'رموز التحديث'
        db_table = 'auth_refresh_tokens'
    
    def __str__(self):
        return f"Refresh Token for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def revoke(self):
        self.is_revoked = True
        self.save()


class LoginHistory(models.Model):
    """
    سجل تسجيل الدخول
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True, null=True)
    login_time = models.DateTimeField(default=timezone.now)
    logout_time = models.DateTimeField(blank=True, null=True)
    is_successful = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'سجل تسجيل الدخول'
        verbose_name_plural = 'سجلات تسجيل الدخول'
        db_table = 'auth_login_history'
        ordering = ['-login_time']
    
    def __str__(self):
        return f"{self.user.email} - {self.login_time}"


class PasswordResetToken(models.Model):
    """
    رموز استرجاع كلمة المرور
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'رمز استرجاع كلمة المرور'
        verbose_name_plural = 'رموز استرجاع كلمة المرور'
        db_table = 'auth_password_reset_tokens'
    
    def __str__(self):
        return f"Password Reset Token for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()


class EmailVerificationToken(models.Model):
    """
    رموز التحقق من البريد الإلكتروني
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    token = models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'رمز التحقق من البريد الإلكتروني'
        verbose_name_plural = 'رموز التحقق من البريد الإلكتروني'
        db_table = 'auth_email_verification_tokens'
    
    def __str__(self):
        return f"Email Verification Token for {self.user.email}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        return not self.is_used and not self.is_expired()
