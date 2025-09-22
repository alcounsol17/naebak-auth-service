'''
# tests_services.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch
from .services import EmailService, GoogleAuthService, UserService
from .models import EmailVerificationToken, PasswordResetToken

User = get_user_model()

class EmailServiceTest(TestCase):
    """
    اختبارات خدمة البريد الإلكتروني
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="emailuser",
            email="email@example.com",
            password="password123",
            is_verified=False
        )

    @patch('django.core.mail.send_mail')
    def test_send_verification_email(self, mock_send_mail):
        """ اختبار إرسال بريد التحقق """
        EmailService.send_verification_email(self.user)
        self.assertTrue(EmailVerificationToken.objects.filter(user=self.user).exists())
        mock_send_mail.assert_called_once()

    @patch('django.core.mail.send_mail')
    def test_send_password_reset_email(self, mock_send_mail):
        """ اختبار إرسال بريد استعادة كلمة المرور """
        EmailService.send_password_reset_email(self.user)
        self.assertTrue(PasswordResetToken.objects.filter(user=self.user).exists())
        mock_send_mail.assert_called_once()

class GoogleAuthServiceTest(TestCase):
    """
    اختبارات خدمة مصادقة جوجل
    """

    @patch('authentication.services.id_token')
    def test_verify_google_token(self, mock_id_token):
        """ اختبار التحقق من رمز جوجل """
        mock_id_token.verify_oauth2_token.return_value = {
            'iss': 'https://accounts.google.com',
            'sub': 'testgoogleid',
            'email': 'google@example.com',
            'name': 'Google User',
            'picture': 'http://example.com/pic.jpg',
            'given_name': 'Google',
            'family_name': 'User',
            'email_verified': True
        }
        google_data = GoogleAuthService.verify_google_token("test_google_token")
        self.assertIsNotNone(google_data)
        self.assertEqual(google_data['email'], 'google@example.com')

    def test_get_or_create_user_from_google(self):
        """ اختبار إنشاء أو جلب مستخدم من جوجل """
        google_data = {
            'google_id': 'testgoogleid123',
            'email': 'newgoogleuser@example.com',
            'first_name': 'New',
            'last_name': 'Google',
            'profile_picture': 'http://example.com/newpic.jpg',
            'is_verified': True
        }
        user, created = GoogleAuthService.get_or_create_user_from_google(google_data, 'citizen')
        self.assertTrue(created)
        self.assertEqual(user.email, 'newgoogleuser@example.com')
        self.assertEqual(user.google_id, 'testgoogleid123')

class UserServiceTest(TestCase):
    """
    اختبارات خدمة المستخدم
    """

    def setUp(self):
        User.objects.create_user(username='user1', email="user1@test.com", password="p1", user_type="citizen")
        User.objects.create_user(username='user2', email="user2@test.com", password="p2", user_type="representative")

    def test_get_user_statistics(self):
        """ اختبار الحصول على إحصائيات المستخدمين """
        stats = UserService.get_user_statistics()
        self.assertEqual(stats['total_users'], 2)
        self.assertEqual(stats['citizens'], 1)
        self.assertEqual(stats['representatives'], 1)
'''
