from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import LoginHistory, PasswordResetToken, EmailVerificationToken
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer,
    ChangePasswordSerializer, RefreshTokenSerializer, LoginHistorySerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, EmailVerificationSerializer,
    ResendVerificationSerializer, GoogleAuthSerializer
)
from .authentication import JWTTokenGenerator
from .services import EmailService, GoogleAuthService, UserService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    الحصول على عنوان IP الخاص بالعميل
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    تسجيل مستخدم جديد
    """
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # إرسال بريد التحقق
        EmailService.send_verification_email(user)
        
        # تسجيل عملية التسجيل
        logger.info(f"New user registered: {user.email}")
        
        # إنشاء رموز المصادقة
        tokens = JWTTokenGenerator.generate_tokens(user)
        
        # تسجيل عملية تسجيل الدخول الأولى
        LoginHistory.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_successful=True
        )
        
        # تحديث آخر IP للدخول
        user.last_login_ip = get_client_ip(request)
        user.last_login = timezone.now()
        user.save()
        
        return Response({
            'message': 'تم تسجيل المستخدم بنجاح. يرجى التحقق من بريدك الإلكتروني لتفعيل الحساب.',
            'user': UserProfileSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
    
    return Response({
        'message': 'خطأ في البيانات المدخلة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    تسجيل الدخول
    """
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # إنشاء رموز المصادقة
        tokens = JWTTokenGenerator.generate_tokens(user)
        
        # تسجيل عملية تسجيل الدخول
        LoginHistory.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_successful=True
        )
        
        # تحديث آخر IP للدخول
        user.last_login_ip = get_client_ip(request)
        user.last_login = timezone.now()
        user.save()
        
        logger.info(f"User logged in: {user.email}")
        
        return Response({
            'message': 'تم تسجيل الدخول بنجاح',
            'user': UserProfileSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_200_OK)
    
    # تسجيل محاولة دخول فاشلة
    email = request.data.get('email')
    if email:
        try:
            user = User.objects.get(email=email)
            LoginHistory.objects.create(
                user=user,
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                is_successful=False
            )
        except User.DoesNotExist:
            pass
    
    return Response({
        'message': 'بيانات تسجيل الدخول غير صحيحة',
        'errors': serializer.errors
    }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    تسجيل الدخول عبر Google
    """
    serializer = GoogleAuthSerializer(data=request.data)
    
    if serializer.is_valid():
        google_token = serializer.validated_data['google_token']
        user_type = serializer.validated_data['user_type']
        
        # التحقق من رمز Google
        google_data = GoogleAuthService.verify_google_token(google_token)
        
        if not google_data:
            return Response({
                'message': 'رمز Google غير صالح'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # الحصول على المستخدم أو إنشاؤه
        user, created = GoogleAuthService.get_or_create_user_from_google(google_data, user_type)
        
        if not user:
            return Response({
                'message': 'خطأ في إنشاء الحساب'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # إنشاء رموز المصادقة
        tokens = JWTTokenGenerator.generate_tokens(user)
        
        # تسجيل عملية تسجيل الدخول
        LoginHistory.objects.create(
            user=user,
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            is_successful=True
        )
        
        # تحديث آخر IP للدخول
        user.last_login_ip = get_client_ip(request)
        user.last_login = timezone.now()
        user.save()
        
        message = 'تم إنشاء الحساب وتسجيل الدخول بنجاح' if created else 'تم تسجيل الدخول بنجاح'
        logger.info(f"Google auth successful for {user.email}, created: {created}")
        
        return Response({
            'message': message,
            'user': UserProfileSerializer(user).data,
            'tokens': tokens
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': 'بيانات غير صحيحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    """
    طلب استرجاع كلمة المرور
    """
    serializer = ForgotPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # إرسال بريد استرجاع كلمة المرور
        if EmailService.send_password_reset_email(user):
            logger.info(f"Password reset requested for {user.email}")
            return Response({
                'message': 'تم إرسال رابط استرجاع كلمة المرور إلى بريدك الإلكتروني'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'خطأ في إرسال البريد الإلكتروني'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'message': 'بيانات غير صحيحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    """
    إعادة تعيين كلمة المرور
    """
    serializer = ResetPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        reset_token = serializer.reset_token
        new_password = serializer.validated_data['new_password']
        
        # تحديث كلمة المرور
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        # تعيين الرمز كمستخدم
        reset_token.is_used = True
        reset_token.save()
        
        logger.info(f"Password reset successful for {user.email}")
        
        return Response({
            'message': 'تم إعادة تعيين كلمة المرور بنجاح'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': 'بيانات غير صحيحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_email(request):
    """
    التحقق من البريد الإلكتروني
    """
    serializer = EmailVerificationSerializer(data=request.data)
    
    if serializer.is_valid():
        verification_token = serializer.verification_token
        
        # تفعيل الحساب
        user = verification_token.user
        user.is_verified = True
        user.save()
        
        # تعيين الرمز كمستخدم
        verification_token.is_used = True
        verification_token.save()
        
        logger.info(f"Email verified for {user.email}")
        
        return Response({
            'message': 'تم تفعيل الحساب بنجاح'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': 'بيانات غير صحيحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_verification(request):
    """
    إعادة إرسال رمز التحقق
    """
    serializer = ResendVerificationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.user
        
        # إرسال بريد التحقق
        if EmailService.send_verification_email(user):
            logger.info(f"Verification email resent to {user.email}")
            return Response({
                'message': 'تم إعادة إرسال رمز التحقق إلى بريدك الإلكتروني'
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'خطأ في إرسال البريد الإلكتروني'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({
        'message': 'بيانات غير صحيحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    """
    تحديث رمز الوصول
    """
    serializer = RefreshTokenSerializer(data=request.data)
    
    if serializer.is_valid():
        refresh_token = serializer.validated_data['refresh_token']
        
        try:
            tokens = JWTTokenGenerator.refresh_access_token(refresh_token)
            
            return Response({
                'message': 'تم تحديث الرمز بنجاح',
                'tokens': tokens
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'message': 'فشل في تحديث الرمز',
                'error': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response({
        'message': 'بيانات غير صحيحة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    تسجيل الخروج
    """
    # إلغاء رمز التحديث إذا تم إرساله
    refresh_token = request.data.get('refresh_token')
    if refresh_token:
        JWTTokenGenerator.revoke_refresh_token(refresh_token)
    
    # تحديث سجل تسجيل الدخول
    try:
        login_history = LoginHistory.objects.filter(
            user=request.user,
            logout_time__isnull=True
        ).order_by('-login_time').first()
        
        if login_history:
            login_history.logout_time = timezone.now()
            login_history.save()
    except Exception:
        pass
    
    logger.info(f"User logged out: {request.user.email}")
    
    return Response({
        'message': 'تم تسجيل الخروج بنجاح'
    }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    عرض وتحديث الملف الشخصي
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    تغيير كلمة المرور
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        logger.info(f"Password changed for user: {user.email}")
        
        return Response({
            'message': 'تم تغيير كلمة المرور بنجاح'
        }, status=status.HTTP_200_OK)
    
    return Response({
        'message': 'خطأ في البيانات المدخلة',
        'errors': serializer.errors
    }, status=status.HTTP_400_BAD_REQUEST)


class LoginHistoryView(generics.ListAPIView):
    """
    عرض سجل تسجيل الدخول
    """
    serializer_class = LoginHistorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LoginHistory.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_info(request):
    """
    الحصول على معلومات المستخدم الحالي
    """
    serializer = UserProfileSerializer(request.user)
    return Response({
        'user': serializer.data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def user_statistics(request):
    """
    الحصول على إحصائيات المستخدمين
    """
    stats = UserService.get_user_statistics()
    if stats:
        return Response(stats, status=status.HTTP_200_OK)
    else:
        return Response({
            'message': 'خطأ في الحصول على الإحصائيات'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    فحص صحة الخدمة
    """
    return Response({
        'status': 'healthy',
        'service': 'naebak-auth-service',
        'version': '2.0.0',
        'timestamp': timezone.now()
    }, status=status.HTTP_200_OK)
