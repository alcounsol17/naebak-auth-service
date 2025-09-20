from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, RefreshToken, LoginHistory


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    إدارة المستخدمين في لوحة الإدارة
    """
    list_display = ['email', 'username', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_active', 'created_at']
    list_filter = ['user_type', 'is_verified', 'is_active', 'created_at', 'governorate']
    search_fields = ['email', 'username', 'first_name', 'last_name', 'national_id']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('معلومات إضافية', {
            'fields': ('phone', 'user_type', 'national_id', 'governorate', 'city', 'address', 'birth_date', 'profile_picture')
        }),
        ('حالة التحقق', {
            'fields': ('is_verified', 'verification_token')
        }),
        ('معلومات النظام', {
            'fields': ('last_login_ip', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login_ip']


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    """
    إدارة رموز التحديث
    """
    list_display = ['user', 'created_at', 'expires_at', 'is_revoked']
    list_filter = ['is_revoked', 'created_at', 'expires_at']
    search_fields = ['user__email', 'user__username']
    readonly_fields = ['token', 'created_at']
    ordering = ['-created_at']


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    """
    إدارة سجل تسجيل الدخول
    """
    list_display = ['user', 'ip_address', 'login_time', 'logout_time', 'is_successful']
    list_filter = ['is_successful', 'login_time']
    search_fields = ['user__email', 'user__username', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'login_time', 'logout_time', 'is_successful']
    ordering = ['-login_time']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
