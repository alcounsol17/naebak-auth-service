"""
نظام المراقبة والمقاييس
"""
import logging
import time
import uuid
from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from prometheus_client import Counter, Histogram, generate_latest

logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds", "HTTP request duration", ["method", "endpoint"]
)

AUTH_OPERATIONS = Counter(
    "auth_operations_total",
    "Authentication operations",
    ["operation", "status", "user_type"],
)

FAILED_LOGIN_ATTEMPTS = Counter(
    "failed_login_attempts_total", "Failed login attempts", ["reason"]
)

ACTIVE_SESSIONS = Counter("active_sessions_total", "Active user sessions")


class MonitoringMiddleware(MiddlewareMixin):
    """
    Middleware للمراقبة وجمع المقاييس
    """

    def process_request(self, request: HttpRequest) -> None:
        """
        معالجة الطلب وإضافة معرف فريد
        """
        request.start_time = time.time()
        request.correlation_id = str(uuid.uuid4())

        # إضافة correlation ID للسجلات
        logger.info(
            "Request started",
            extra={
                "correlation_id": request.correlation_id,
                "method": request.method,
                "path": request.path,
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "remote_addr": self.get_client_ip(request),
            },
        )

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """
        معالجة الاستجابة وتسجيل المقاييس
        """
        if hasattr(request, "start_time"):
            duration = time.time() - request.start_time

            # تسجيل مقاييس Prometheus
            endpoint = self.get_endpoint_name(request.path)
            REQUEST_COUNT.labels(
                method=request.method, endpoint=endpoint, status=response.status_code
            ).inc()

            REQUEST_DURATION.labels(method=request.method, endpoint=endpoint).observe(
                duration
            )

            # تسجيل تفاصيل الاستجابة
            logger.info(
                "Request completed",
                extra={
                    "correlation_id": getattr(request, "correlation_id", "unknown"),
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration": duration,
                    "response_size": len(response.content),
                },
            )

        return response

    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        """
        الحصول على IP الحقيقي للعميل
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    @staticmethod
    def get_endpoint_name(path: str) -> str:
        """
        تحويل المسار إلى اسم endpoint مبسط
        """
        if path.startswith("/api/auth/"):
            if "login" in path:
                return "auth_login"
            elif "register" in path:
                return "auth_register"
            elif "logout" in path:
                return "auth_logout"
            elif "refresh" in path:
                return "auth_refresh"
            elif "profile" in path:
                return "auth_profile"
            elif "health" in path:
                return "health_check"
            else:
                return "auth_other"
        return "other"


class AuthMetricsLogger:
    """
    مسجل مقاييس المصادقة
    """

    @staticmethod
    def log_login_attempt(
        user_email: str, success: bool, user_type: Optional[str] = None, reason: str = ""
    ):
        """
        تسجيل محاولة تسجيل دخول
        """
        status = "success" if success else "failure"
        user_type = user_type or "unknown"

        AUTH_OPERATIONS.labels(
            operation="login", status=status, user_type=user_type
        ).inc()

        if not success:
            FAILED_LOGIN_ATTEMPTS.labels(reason=reason).inc()

        logger.info(
            "Login attempt",
            extra={
                "operation": "login",
                "user_email": user_email,
                "success": success,
                "user_type": user_type,
                "reason": reason,
            },
        )

    @staticmethod
    def log_registration(user_email: str, user_type: str, success: bool):
        """
        تسجيل محاولة تسجيل مستخدم جديد
        """
        status = "success" if success else "failure"

        AUTH_OPERATIONS.labels(
            operation="register", status=status, user_type=user_type
        ).inc()

        logger.info(
            "User registration",
            extra={
                "operation": "register",
                "user_email": user_email,
                "user_type": user_type,
                "success": success,
            },
        )

    @staticmethod
    def log_logout(user_email: str, user_type: str):
        """
        تسجيل عملية تسجيل خروج
        """
        AUTH_OPERATIONS.labels(
            operation="logout", status="success", user_type=user_type
        ).inc()

        logger.info(
            "User logout",
            extra={"operation": "logout", "user_email": user_email, "user_type": user_type},
        )

    @staticmethod
    def log_password_change(user_email: str, success: bool):
        """
        تسجيل تغيير كلمة المرور
        """
        status = "success" if success else "failure"

        AUTH_OPERATIONS.labels(
            operation="password_change", status=status, user_type="unknown"
        ).inc()

        logger.info(
            "Password change",
            extra={
                "operation": "password_change",
                "user_email": user_email,
                "success": success,
            },
        )

    @staticmethod
    def log_security_event(event_type: str, user_email: str, details: dict):
        """
        تسجيل حدث أمني
        """
        security_logger = logging.getLogger("security")
        security_logger.warning(
            f"Security event: {event_type}",
            extra={
                "event_type": event_type,
                "user_email": user_email,
                "details": details,
            },
        )


def metrics_view(request):
    """
    عرض مقاييس Prometheus
    """
    from django.http import HttpResponse

    return HttpResponse(generate_latest(), content_type="text/plain")


class HealthChecker:
    """
    فاحص صحة النظام
    """

    @staticmethod
    def check_database():
        """
        فحص اتصال قاعدة البيانات
        """
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True, "Database connection OK"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"

    @staticmethod
    def check_redis():
        """
        فحص اتصال Redis
        """
        try:
            from django.core.cache import cache

            cache.set("health_check", "ok", 10)
            result = cache.get("health_check")
            if result == "ok":
                return True, "Redis connection OK"
            else:
                return False, "Redis connection failed"
        except Exception as e:
            return False, f"Redis connection failed: {str(e)}"

    @staticmethod
    def get_system_health():
        """
        الحصول على حالة صحة النظام الشاملة
        """
        checks = {
            "database": HealthChecker.check_database(),
            "redis": HealthChecker.check_redis(),
        }

        all_healthy = all(check[0] for check in checks.values())
        status = "healthy" if all_healthy else "unhealthy"

        return {
            "status": status,
            "checks": {name: {"status": check[0], "message": check[1]} for name, check in checks.items()},
            "timestamp": time.time(),
        }
