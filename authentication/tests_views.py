'''
# tests_views.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch

User = get_user_model()

class AuthAPITest(APITestCase):
    """
    اختبارات واجهات برمجة التطبيقات للمصادقة
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123",
            first_name="Test",
            last_name="User"
        )

    def test_registration_api(self):
        """ اختبار API تسجيل مستخدم جديد """
        url = reverse("register")
        data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewStrongPassword123",
            "password_confirm": "NewStrongPassword123",
            "first_name": "New",
            "last_name": "User",
            "user_type": "citizen"
        }
        with patch('authentication.services.EmailService.send_verification_email') as mock_send_email:
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertIn("access_token", response.data["tokens"])
            mock_send_email.assert_called_once()

    def test_login_api(self):
        """ اختبار API تسجيل الدخول """
        url = reverse("login")
        data = {"email": "test@example.com", "password": "StrongPassword123"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.data["tokens"])

    def test_refresh_token_api(self):
        """ اختبار API تحديث رمز الوصول """
        login_url = reverse("login")
        login_data = {"email": "test@example.com", "password": "StrongPassword123"}
        login_response = self.client.post(login_url, login_data, format='json')
        refresh_token = login_response.data["tokens"]["refresh_token"]

        refresh_url = reverse("refresh_token")
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = self.client.post(refresh_url, refresh_data, format='json')
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", refresh_response.data["tokens"])

    def test_user_profile_api(self):
        """ اختبار API عرض وتحديث الملف الشخصي """
        self.client.force_authenticate(user=self.user)
        url = reverse("user_profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)

        update_data = {"first_name": "Updated"}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")

    def test_change_password_api(self):
        """ اختبار API تغيير كلمة المرور """
        self.client.force_authenticate(user=self.user)
        url = reverse("change_password")
        data = {
            "old_password": "StrongPassword123",
            "new_password": "ANewStrongerPassword456",
            "new_password_confirm": "ANewStrongerPassword456"
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.logout()
        login_url = reverse("login")
        login_data = {"email": "test@example.com", "password": "ANewStrongerPassword456"}
        login_response = self.client.post(login_url, login_data, format='json')
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
'''
