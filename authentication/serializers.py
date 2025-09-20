from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, LoginHistory
import re


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    مسلسل تسجيل المستخدم الجديد
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'user_type',
            'national_id', 'governorate', 'city', 'address', 'birth_date'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        """
        التحقق من صحة البريد الإلكتروني
        """
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("هذا البريد الإلكتروني مستخدم بالفعل")
        return value
    
    def validate_username(self, value):
        """
        التحقق من صحة اسم المستخدم
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("اسم المستخدم هذا مستخدم بالفعل")
        return value
    
    def validate_national_id(self, value):
        """
        التحقق من صحة الرقم القومي
        """
        if value:
            if not re.match(r'^\d{14}$', value):
                raise serializers.ValidationError("الرقم القومي يجب أن يكون 14 رقماً")
            
            if User.objects.filter(national_id=value).exists():
                raise serializers.ValidationError("هذا الرقم القومي مستخدم بالفعل")
        
        return value
    
    def validate_phone(self, value):
        """
        التحقق من صحة رقم الهاتف
        """
        if value:
            # التحقق من تنسيق رقم الهاتف المصري
            if not re.match(r'^(\+20|0)?1[0125]\d{8}$', value):
                raise serializers.ValidationError("رقم الهاتف غير صحيح")
        
        return value
    
    def validate(self, attrs):
        """
        التحقق من تطابق كلمات المرور
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("كلمات المرور غير متطابقة")
        
        return attrs
    
    def create(self, validated_data):
        """
        إنشاء مستخدم جديد
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    مسلسل تسجيل الدخول
    """
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """
        التحقق من بيانات تسجيل الدخول
        """
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError("بيانات تسجيل الدخول غير صحيحة")
            
            if not user.is_active:
                raise serializers.ValidationError("حساب المستخدم غير مفعل")
            
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError("يجب إدخال البريد الإلكتروني وكلمة المرور")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    مسلسل الملف الشخصي للمستخدم
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'phone', 'user_type', 'national_id', 'governorate', 'city',
            'address', 'birth_date', 'profile_picture', 'is_verified',
            'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['id', 'username', 'email', 'user_type', 'is_verified', 'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    """
    مسلسل تغيير كلمة المرور
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        """
        التحقق من كلمة المرور القديمة
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("كلمة المرور القديمة غير صحيحة")
        return value
    
    def validate(self, attrs):
        """
        التحقق من تطابق كلمة المرور الجديدة
        """
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("كلمات المرور الجديدة غير متطابقة")
        return attrs


class RefreshTokenSerializer(serializers.Serializer):
    """
    مسلسل تحديث الرمز المميز
    """
    refresh_token = serializers.CharField()


class LoginHistorySerializer(serializers.ModelSerializer):
    """
    مسلسل سجل تسجيل الدخول
    """
    class Meta:
        model = LoginHistory
        fields = ['ip_address', 'user_agent', 'login_time', 'logout_time', 'is_successful']
