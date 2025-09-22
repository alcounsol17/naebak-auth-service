from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.urls import reverse
from .models import PasswordResetToken, EmailVerificationToken, User
from datetime import timedelta
import logging
import requests
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

logger = logging.getLogger(__name__)


class EmailService:
    """
    خدمة إرسال البريد الإلكتروني
    """
    
    @staticmethod
    def send_verification_email(user):
        """
        إرسال بريد التحقق من البريد الإلكتروني
        """
        try:
            # إنشاء رمز التحقق
            verification_token = EmailVerificationToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            # إعداد محتوى البريد
            subject = 'تفعيل حساب منصة نائبك'
            verification_url = f"{settings.FRONTEND_URL}/verify-email/{verification_token.token}"
            
            message = f"""
            مرحباً {user.full_name},
            
            شكراً لك على التسجيل في منصة نائبك. لتفعيل حسابك، يرجى النقر على الرابط التالي:
            
            {verification_url}
            
            هذا الرابط صالح لمدة 24 ساعة فقط.
            
            إذا لم تقم بإنشاء هذا الحساب، يرجى تجاهل هذا البريد.
            
            مع تحيات فريق منصة نائبك
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Verification email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
            return False
    
    @staticmethod
    def send_password_reset_email(user):
        """
        إرسال بريد استرجاع كلمة المرور
        """
        try:
            # إنشاء رمز استرجاع كلمة المرور
            reset_token = PasswordResetToken.objects.create(
                user=user,
                expires_at=timezone.now() + timedelta(hours=1)
            )
            
            # إعداد محتوى البريد
            subject = 'استرجاع كلمة المرور - منصة نائبك'
            reset_url = f"{settings.FRONTEND_URL}/reset-password/{reset_token.token}"
            
            message = f"""
            مرحباً {user.full_name},
            
            تلقينا طلباً لإعادة تعيين كلمة المرور الخاصة بحسابك في منصة نائبك.
            
            لإعادة تعيين كلمة المرور، يرجى النقر على الرابط التالي:
            
            {reset_url}
            
            هذا الرابط صالح لمدة ساعة واحدة فقط.
            
            إذا لم تطلب إعادة تعيين كلمة المرور، يرجى تجاهل هذا البريد.
            
            مع تحيات فريق منصة نائبك
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Password reset email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return False


class GoogleAuthService:
    """
    خدمة المصادقة عبر Google
    """
    
    @staticmethod
    def verify_google_token(token):
        """
        التحقق من رمز Google والحصول على معلومات المستخدم
        """
        try:
            # التحقق من الرمز مع Google
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                settings.GOOGLE_OAUTH2_CLIENT_ID
            )
            
            # التحقق من صحة الجهة المصدرة
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
            
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'first_name': idinfo.get('given_name', ''),
                'last_name': idinfo.get('family_name', ''),
                'profile_picture': idinfo.get('picture', ''),
                'is_verified': idinfo.get('email_verified', False)
            }
            
        except ValueError as e:
            logger.error(f"Invalid Google token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error verifying Google token: {str(e)}")
            return None
    
    @staticmethod
    def get_or_create_user_from_google(google_data, user_type='citizen'):
        """
        الحصول على المستخدم أو إنشاؤه من بيانات Google
        """
        try:
            # البحث عن المستخدم بمعرف Google أولاً
            try:
                user = User.objects.get(google_id=google_data['google_id'])
                return user, False
            except User.DoesNotExist:
                pass
            
            # البحث عن المستخدم بالبريد الإلكتروني
            try:
                user = User.objects.get(email=google_data['email'])
                # ربط الحساب الموجود بـ Google
                user.google_id = google_data['google_id']
                user.google_email = google_data['email']
                if not user.is_verified and google_data['is_verified']:
                    user.is_verified = True
                if not user.profile_picture and google_data['profile_picture']:
                    user.profile_picture = google_data['profile_picture']
                user.save()
                return user, False
            except User.DoesNotExist:
                pass
            
            # إنشاء مستخدم جديد
            username = google_data['email'].split('@')[0]
            # التأكد من عدم تكرار اسم المستخدم
            counter = 1
            original_username = username
            while User.objects.filter(username=username).exists():
                username = f"{original_username}{counter}"
                counter += 1
            
            user = User.objects.create_user(
                username=username,
                email=google_data['email'],
                first_name=google_data['first_name'],
                last_name=google_data['last_name'],
                user_type=user_type,
                google_id=google_data['google_id'],
                google_email=google_data['email'],
                profile_picture=google_data['profile_picture'],
                is_verified=google_data['is_verified']
            )
            
            return user, True
            
        except Exception as e:
            logger.error(f"Error creating user from Google data: {str(e)}")
            return None, False


class TokenService:
    """
    خدمة إدارة الرموز
    """
    
    @staticmethod
    def cleanup_expired_tokens():
        """
        تنظيف الرموز المنتهية الصلاحية
        """
        try:
            # حذف رموز استرجاع كلمة المرور المنتهية الصلاحية
            expired_password_tokens = PasswordResetToken.objects.filter(
                expires_at__lt=timezone.now()
            )
            password_count = expired_password_tokens.count()
            expired_password_tokens.delete()
            
            # حذف رموز التحقق من البريد الإلكتروني المنتهية الصلاحية
            expired_verification_tokens = EmailVerificationToken.objects.filter(
                expires_at__lt=timezone.now()
            )
            verification_count = expired_verification_tokens.count()
            expired_verification_tokens.delete()
            
            logger.info(f"Cleaned up {password_count} password reset tokens and {verification_count} verification tokens")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")


class UserService:
    """
    خدمة إدارة المستخدمين
    """
    
    @staticmethod
    def get_user_statistics():
        """
        الحصول على إحصائيات المستخدمين
        """
        try:
            total_users = User.objects.count()
            verified_users = User.objects.filter(is_verified=True).count()
            citizens = User.objects.filter(user_type='citizen').count()
            representatives = User.objects.filter(user_type='representative').count()
            admins = User.objects.filter(user_type='admin').count()
            
            return {
                'total_users': total_users,
                'verified_users': verified_users,
                'unverified_users': total_users - verified_users,
                'citizens': citizens,
                'representatives': representatives,
                'admins': admins
            }
            
        except Exception as e:
            logger.error(f"Error getting user statistics: {str(e)}")
            return None
