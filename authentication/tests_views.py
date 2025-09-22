# tests_views.py

import time
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.test import TestCase

from .authentication import JWTTokenGenerator
from .models import EmailVerificationToken, PasswordResetToken, RefreshToken

User = get_user_model()


class AuthAPITest(APITestCase):
    """
    اختبارات واجهات برمجة التطبيقات للمصادقة
    """

    def setUp(self):
        """إعداد البيانات للاختبارات"""
        cache.clear()  # تنظيف cache قبل كل اختبار
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
            first_name="Test",
            last_name="User",
            user_type="citizen",
        )

    def test_registration_api_success(self):
        """اختبار API تسجيل مستخدم جديد - حالة النجاح"""
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewStrongPassword123!",
            "password_confirm": "NewStrongPassword123!",
            "first_name": "New",
            "last_name": "User",
            "user_type": "citizen",
        }
        with patch(
            "authentication.services.EmailService.send_verification_email"
        ) as mock_send_email:
            mock_send_email.return_value = True
            response = self.client.post(url, data, format="json")
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn("access_token", response.data["tokens"])
            mock_send_email.assert_called_once()

    def test_registration_api_duplicate_email(self):
        """اختبار تسجيل مستخدم ببريد إلكتروني موجود"""
        url = reverse("register")
        data = {
            "username": "anotheruser",
            "email": "test@example.com",  # بريد موجود مسبقاً
            "password": "NewStrongPassword123!",
            "password_confirm": "NewStrongPassword123!",
            "first_name": "Another",
            "last_name": "User",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_api_weak_password(self):
        """اختبار تسجيل مستخدم بكلمة مرور ضعيفة"""
        url = reverse("register")
        data = {
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "123",  # كلمة مرور ضعيفة
            "password_confirm": "123",
            "first_name": "Weak",
            "last_name": "User",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_api_success(self):
        """اختبار API تسجيل الدخول - حالة النجاح"""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "StrongPassword123!"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data["tokens"])
        self.assertIn("refresh_token", response.data["tokens"])

    def test_login_api_invalid_credentials(self):
        """اختبار تسجيل الدخول ببيانات خاطئة"""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "WrongPassword"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_api_nonexistent_user(self):
        """اختبار تسجيل الدخول بمستخدم غير موجود"""
        url = reverse("login")
        data = {"email": "nonexistent@example.com", "password": "SomePassword123!"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_api_success(self):
        """اختبار API تحديث رمز الوصول - حالة النجاح"""
        # تسجيل دخول أولاً للحصول على refresh token
        login_url = reverse("login")
        login_data = {"email": "test@example.com", "password": "StrongPassword123!"}
        login_response = self.client.post(login_url, login_data, format="json")
        refresh_token = login_response.data["tokens"]["refresh_token"]

        # تحديث الرمز
        refresh_url = reverse("refresh_token")
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = self.client.post(refresh_url, refresh_data, format="json")
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", refresh_response.data["tokens"])

    def test_refresh_token_api_invalid_token(self):
        """اختبار تحديث الرمز برمز غير صالح"""
        refresh_url = reverse("refresh_token")
        refresh_data = {"refresh_token": "invalid_token"}
        refresh_response = self.client.post(refresh_url, refresh_data, format="json")
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_api_get(self):
        """اختبار API عرض الملف الشخصي"""
        self.client.force_authenticate(user=self.user)
        url = reverse("user_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["first_name"], self.user.first_name)

    def test_user_profile_api_update(self):
        """اختبار API تحديث الملف الشخصي"""
        self.client.force_authenticate(user=self.user)
        url = reverse("user_profile")
        update_data = {"first_name": "Updated", "last_name": "Name"}
        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")
        self.assertEqual(response.data["last_name"], "Name")

    def test_user_profile_api_unauthorized(self):
        """اختبار الوصول للملف الشخصي بدون مصادقة"""
        url = reverse("user_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_password_api_success(self):
        """اختبار API تغيير كلمة المرور - حالة النجاح"""
        self.client.force_authenticate(user=self.user)
        url = reverse("change_password")
        data = {
            "old_password": "StrongPassword123!",
            "new_password": "ANewStrongerPassword456!",
            "new_password_confirm": "ANewStrongerPassword456!",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # التحقق من أن كلمة المرور تغيرت فعلاً
        self.client.logout()
        login_url = reverse("login")
        login_data = {
            "email": "test@example.com",
            "password": "ANewStrongerPassword456!",
        }
        login_response = self.client.post(login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_change_password_api_wrong_old_password(self):
        """اختبار تغيير كلمة المرور بكلمة مرور قديمة خاطئة"""
        self.client.force_authenticate(user=self.user)
        url = reverse("change_password")
        data = {
            "old_password": "WrongOldPassword",
            "new_password": "ANewStrongerPassword456!",
            "new_password_confirm": "ANewStrongerPassword456!",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_api_weak_new_password(self):
        """اختبار تغيير كلمة المرور بكلمة مرور جديدة ضعيفة"""
        self.client.force_authenticate(user=self.user)
        url = reverse("change_password")
        data = {
            "old_password": "StrongPassword123!",
            "new_password": "123",  # كلمة مرور ضعيفة
            "new_password_confirm": "123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("authentication.services.EmailService.send_password_reset_email")
    def test_forgot_password_api_success(self, mock_send_email):
        """اختبار API نسيان كلمة المرور - حالة النجاح"""
        mock_send_email.return_value = True
        url = reverse("forgot_password")
        data = {"email": "test@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_send_email.assert_called_once()

    def test_forgot_password_api_nonexistent_email(self):
        """اختبار نسيان كلمة المرور ببريد غير موجود"""
        url = reverse("forgot_password")
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_api_success(self):
        """اختبار API تسجيل الخروج"""
        # تسجيل دخول أولاً
        login_url = reverse("login")
        login_data = {"email": "test@example.com", "password": "StrongPassword123!"}
        login_response = self.client.post(login_url, login_data, format="json")
        refresh_token = login_response.data["tokens"]["refresh_token"]

        # تسجيل خروج
        self.client.force_authenticate(user=self.user)
        logout_url = reverse("logout")
        logout_data = {"refresh_token": refresh_token}
        response = self.client.post(logout_url, logout_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health_check_api(self):
        """اختبار API فحص الصحة"""
        url = reverse("health_check")
        response = self.client.get(url)
        # في بيئة الاختبار قد يكون 503 بسبب عدم توفر Redis/PostgreSQL
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn("status", response.data)

class RateLimitingTest(TestCase):
    """اختبارات تحديد المعدل - معطلة في بيئة الاختبار"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="Test",
            last_name="User",
            user_type="citizen",
        )

    def test_rate_limiting_disabled_in_tests(self):
        """اختبار أن Rate Limiting معطل في بيئة الاختبار"""
        url = reverse("login")
        data = {"email": "test@example.com", "password": "wrongpassword"}

        # محاولات متعددة - يجب أن تعمل لأن Rate Limiting معطل
        for i in range(10):
            response = self.client.post(url, data, format="json")
            # يجب أن تكون النتيجة 401 (Unauthorized) وليس 429 (Rate Limited)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
