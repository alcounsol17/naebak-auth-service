"""
Middleware للأمان وتحديد المعدل
"""

import logging
import time

from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware للأمان العام
    """

    def process_request(self, request):
        """
        معالجة الطلب قبل الوصول إلى view
        """
        # إضافة headers أمان
        request.META["HTTP_X_FORWARDED_PROTO"] = request.META.get(
            "HTTP_X_FORWARDED_PROTO", "https"
        )

        # تسجيل معلومات الطلب
        logger.info(
            f"Request: {request.method} {request.path} from {self.get_client_ip(request)}"
        )

        return None

    def process_response(self, request, response):
        """
        معالجة الاستجابة قبل الإرسال
        """
        # إضافة security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response

    def process_exception(self, request, exception):
        """
        معالجة الاستثناءات
        """
        if isinstance(exception, Ratelimited):
            logger.warning(
                f"Rate limit exceeded for {self.get_client_ip(request)} on {request.path}"
            )
            return JsonResponse(
                {
                    "error": "تم تجاوز الحد المسموح من الطلبات",
                    "message": "يرجى المحاولة مرة أخرى بعد قليل",
                    "retry_after": 60,
                },
                status=429,
            )

        return None

    @staticmethod
    def get_client_ip(request):
        """
        الحصول على IP الحقيقي للعميل
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class LoginAttemptMiddleware(MiddlewareMixin):
    """
    Middleware لمراقبة محاولات تسجيل الدخول المشبوهة
    """

    def process_request(self, request):
        """
        مراقبة محاولات تسجيل الدخول
        """
        if request.path == "/api/auth/login/" and request.method == "POST":
            client_ip = SecurityMiddleware.get_client_ip(request)

            # فحص محاولات تسجيل الدخول الفاشلة
            failed_attempts_key = f"failed_login_attempts:{client_ip}"
            failed_attempts = cache.get(failed_attempts_key, 0)

            if failed_attempts >= 5:
                logger.warning(
                    f"IP {client_ip} blocked due to too many failed login attempts"
                )
                return JsonResponse(
                    {
                        "error": "تم حظر IP مؤقتاً",
                        "message": "تم تجاوز عدد محاولات تسجيل الدخول المسموحة",
                        "retry_after": 900,  # 15 minutes
                    },
                    status=429,
                )

        return None

    def process_response(self, request, response):
        """
        تسجيل نتائج محاولات تسجيل الدخول
        """
        if request.path == "/api/auth/login/" and request.method == "POST":
            client_ip = SecurityMiddleware.get_client_ip(request)
            failed_attempts_key = f"failed_login_attempts:{client_ip}"

            if response.status_code == 401:  # فشل تسجيل الدخول
                failed_attempts = cache.get(failed_attempts_key, 0)
                cache.set(failed_attempts_key, failed_attempts + 1, 900)  # 15 minutes
                logger.warning(f"Failed login attempt from {client_ip}")
            elif response.status_code == 200:  # نجح تسجيل الدخول
                cache.delete(failed_attempts_key)  # إزالة العداد عند النجاح
                logger.info(f"Successful login from {client_ip}")

        return response
