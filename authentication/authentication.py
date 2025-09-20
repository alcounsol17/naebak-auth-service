import jwt
from datetime import datetime, timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import RefreshToken
import uuid

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    نظام المصادقة باستخدام JWT
    """
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            user_id = payload.get('user_id')
            if not user_id:
                raise AuthenticationFailed('Invalid token payload')
            
            user = User.objects.get(id=user_id)
            
            if not user.is_active:
                raise AuthenticationFailed('User account is disabled')
            
            return (user, token)
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')


class JWTTokenGenerator:
    """
    مولد رموز JWT
    """
    
    @staticmethod
    def generate_access_token(user):
        """
        إنشاء رمز الوصول (Access Token)
        """
        payload = {
            'user_id': user.id,
            'email': user.email,
            'user_type': user.user_type,
            'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_ACCESS_TOKEN_LIFETIME),
            'iat': datetime.utcnow(),
            'type': 'access'
        }
        
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def generate_refresh_token(user):
        """
        إنشاء رمز التحديث (Refresh Token)
        """
        # إنشاء رمز فريد
        token_id = str(uuid.uuid4())
        
        payload = {
            'user_id': user.id,
            'token_id': token_id,
            'exp': datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME),
            'iat': datetime.utcnow(),
            'type': 'refresh'
        }
        
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        
        # حفظ الرمز في قاعدة البيانات
        RefreshToken.objects.create(
            user=user,
            token=token_id,
            expires_at=datetime.utcnow() + timedelta(seconds=settings.JWT_REFRESH_TOKEN_LIFETIME)
        )
        
        return token
    
    @staticmethod
    def generate_tokens(user):
        """
        إنشاء كل من رمز الوصول ورمز التحديث
        """
        access_token = JWTTokenGenerator.generate_access_token(user)
        refresh_token = JWTTokenGenerator.generate_refresh_token(user)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': settings.JWT_ACCESS_TOKEN_LIFETIME
        }
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """
        تحديث رمز الوصول باستخدام رمز التحديث
        """
        try:
            payload = jwt.decode(
                refresh_token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            if payload.get('type') != 'refresh':
                raise AuthenticationFailed('Invalid token type')
            
            user_id = payload.get('user_id')
            token_id = payload.get('token_id')
            
            # التحقق من وجود الرمز في قاعدة البيانات
            refresh_token_obj = RefreshToken.objects.get(
                user_id=user_id,
                token=token_id,
                is_revoked=False
            )
            
            if refresh_token_obj.is_expired():
                refresh_token_obj.revoke()
                raise AuthenticationFailed('Refresh token has expired')
            
            user = User.objects.get(id=user_id)
            
            if not user.is_active:
                raise AuthenticationFailed('User account is disabled')
            
            # إنشاء رمز وصول جديد
            new_access_token = JWTTokenGenerator.generate_access_token(user)
            
            return {
                'access_token': new_access_token,
                'token_type': 'Bearer',
                'expires_in': settings.JWT_ACCESS_TOKEN_LIFETIME
            }
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Refresh token has expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid refresh token')
        except RefreshToken.DoesNotExist:
            raise AuthenticationFailed('Refresh token not found or revoked')
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found')
    
    @staticmethod
    def revoke_refresh_token(refresh_token):
        """
        إلغاء رمز التحديث
        """
        try:
            payload = jwt.decode(
                refresh_token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            token_id = payload.get('token_id')
            
            refresh_token_obj = RefreshToken.objects.get(token=token_id)
            refresh_token_obj.revoke()
            
            return True
            
        except (jwt.InvalidTokenError, RefreshToken.DoesNotExist):
            return False
