# tests_security.py

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class SecurityAPITest(APITestCase):
    """
    اختبارات الأمان والسيناريوهات السلبية
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="secureuser",
            email="secure@example.com",
            password="SecurePassword123",
        )

    def test_login_with_invalid_credentials(self):
        """اختبار تسجيل الدخول ببيانات غير صحيحة"""
        url = reverse("login")
        data = {"email": "secure@example.com", "password": "WrongPassword"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_protected_endpoint_without_token(self):
        """اختبار الوصول لنقطة نهاية محميّة بدون رمز"""
        url = reverse("user_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_registration_with_existing_email(self):
        """اختبار التسجيل ببريد إلكتروني موجود مسبقًا"""
        url = reverse("register")
        data = {
            "username": "anotheruser",
            "email": "secure@example.com",
            "password": "NewPassword123",
            "password_confirm": "NewPassword123",
            "first_name": "Another",
            "last_name": "User",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_with_invalid_token(self):
        """اختبار إعادة تعيين كلمة المرور برمز غير صالح"""
        url = reverse("reset_password")
        data = {
            "token": "invalidtoken",
            "new_password": "somepassword",
            "new_password_confirm": "somepassword",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
