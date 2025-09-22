# tests_performance.py

import time

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase

User = get_user_model()


class PerformanceAPITest(APITestCase):
    """
    اختبارات الأداء الأساسية
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="perfuser", email="perf@example.com", password="PerfPassword123"
        )

    def test_login_performance(self):
        """اختبار أداء تسجيل الدخول"""
        url = reverse("login")
        data = {"email": "perf@example.com", "password": "PerfPassword123"}

        start_time = time.time()
        response = self.client.post(url, data, format="json")
        end_time = time.time()

        duration = end_time - start_time

        self.assertEqual(response.status_code, 200)
        # نتوقع أن تكون الاستجابة سريعة (أقل من 500 مللي ثانية)
        self.assertLess(duration, 0.5)
        print(f"\nLogin API response time: {duration:.4f} seconds")

    def test_profile_view_performance(self):
        """اختبار أداء عرض الملف الشخصي"""
        self.client.force_authenticate(user=self.user)
        url = reverse("user_profile")

        start_time = time.time()
        response = self.client.get(url)
        end_time = time.time()

        duration = end_time - start_time

        self.assertEqual(response.status_code, 200)
        # نتوقع أن تكون الاستجابة سريعة جداً (أقل من 200 مللي ثانية)
        self.assertLess(duration, 0.2)
        print(f"Profile View API response time: {duration:.4f} seconds")
