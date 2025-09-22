# tests_services.py

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.utils import timezone

from .models import EmailVerificationToken, PasswordResetToken
from .services import EmailService, GoogleAuthService, UserService

User = get_user_model()


class EmailServiceTest(TestCase):
    """
    اختبارات خدمة البريد الإلكتروني
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="emailuser",
            email="email@example.com",
            password="StrongPassword123!",
            first_name="Email",
            last_name="User",
            is_verified=False,
        )

    @patch("authentication.services.send_mail")
    def test_send_verification_email_success(self, mock_send_mail):
        """اختبار إرسال بريد التحقق - حالة النجاح"""
        mock_send_mail.return_value = True
        result = EmailService.send_verification_email(self.user)

        self.assertTrue(result)
        self.assertTrue(EmailVerificationToken.objects.filter(user=self.user).exists())
        mock_send_mail.assert_called_once()

    @patch("authentication.services.send_mail")
    def test_send_verification_email_failure(self, mock_send_mail):
        """اختبار إرسال بريد التحقق - حالة الفشل"""
        mock_send_mail.side_effect = Exception("Email sending failed")
        result = EmailService.send_verification_email(self.user)

        self.assertFalse(result)
        mock_send_mail.assert_called_once()

    @patch("authentication.services.send_mail")
    def test_send_password_reset_email_success(self, mock_send_mail):
        """اختبار إرسال بريد استعادة كلمة المرور - حالة النجاح"""
        mock_send_mail.return_value = True
        result = EmailService.send_password_reset_email(self.user)

        self.assertTrue(result)
        self.assertTrue(PasswordResetToken.objects.filter(user=self.user).exists())
        mock_send_mail.assert_called_once()

    @patch("authentication.services.send_mail")
    def test_send_password_reset_email_failure(self, mock_send_mail):
        """اختبار إرسال بريد استعادة كلمة المرور - حالة الفشل"""
        mock_send_mail.side_effect = Exception("Email sending failed")
        result = EmailService.send_password_reset_email(self.user)

        self.assertFalse(result)
        mock_send_mail.assert_called_once()

    def test_email_verification_token_creation(self):
        """اختبار إنشاء رمز التحقق من البريد الإلكتروني"""
        token = EmailVerificationToken.objects.create(
            user=self.user, expires_at=timezone.now() + timedelta(hours=24)
        )
        
        self.assertIsNotNone(token.token)
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.is_used)

    def test_password_reset_token_creation(self):
        """اختبار إنشاء رمز استعادة كلمة المرور"""
        token = PasswordResetToken.objects.create(
            user=self.user, expires_at=timezone.now() + timedelta(hours=1)
        )
        
        self.assertIsNotNone(token.token)
        self.assertEqual(token.user, self.user)
        self.assertFalse(token.is_used)


class GoogleAuthServiceTest(TestCase):
    """
    اختبارات خدمة مصادقة جوجل
    """

    @patch("authentication.services.id_token")
    def test_verify_google_token_success(self, mock_id_token):
        """اختبار التحقق من رمز جوجل - حالة النجاح"""
        mock_id_token.verify_oauth2_token.return_value = {
            "iss": "https://accounts.google.com",
            "sub": "testgoogleid",
            "email": "google@example.com",
            "name": "Google User",
            "picture": "http://example.com/pic.jpg",
            "given_name": "Google",
            "family_name": "User",
            "email_verified": True,
        }

        google_data = GoogleAuthService.verify_google_token("test_google_token")
        self.assertIsNotNone(google_data)
        self.assertEqual(google_data["email"], "google@example.com")
        self.assertEqual(google_data["google_id"], "testgoogleid")

    @patch("authentication.services.id_token")
    def test_verify_google_token_invalid(self, mock_id_token):
        """اختبار التحقق من رمز جوجل غير صالح"""
        mock_id_token.verify_oauth2_token.side_effect = Exception("Invalid token")

        google_data = GoogleAuthService.verify_google_token("invalid_token")
        self.assertIsNone(google_data)

    def test_get_or_create_user_from_google_new_user(self):
        """اختبار إنشاء مستخدم جديد من جوجل"""
        google_data = {
            "google_id": "testgoogleid123",
            "email": "newgoogleuser@example.com",
            "first_name": "New",
            "last_name": "Google",
            "profile_picture": "http://example.com/newpic.jpg",
            "is_verified": True,
        }

        user, created = GoogleAuthService.get_or_create_user_from_google(
            google_data, "citizen"
        )

        self.assertTrue(created)
        self.assertEqual(user.email, "newgoogleuser@example.com")
        self.assertEqual(user.google_id, "testgoogleid123")
        self.assertTrue(user.is_verified)

    def test_get_or_create_user_from_google_existing_user(self):
        """اختبار جلب مستخدم موجود من جوجل"""
        # إنشاء مستخدم موجود
        existing_user = User.objects.create_user(
            username="googleuser",
            email="existing@example.com",
            google_id="existinggoogleid",
        )

        google_data = {
            "google_id": "existinggoogleid",
            "email": "existing@example.com",
            "first_name": "Existing",
            "last_name": "User",
            "profile_picture": "http://example.com/pic.jpg",
            "is_verified": True,
        }

        user, created = GoogleAuthService.get_or_create_user_from_google(
            google_data, "citizen"
        )

        self.assertFalse(created)
        self.assertEqual(user.id, existing_user.id)


class UserServiceTest(TestCase):
    """
    اختبارات خدمة المستخدم
    """

    def setUp(self):
        self.citizen1 = User.objects.create_user(
            username="citizen1",
            email="citizen1@test.com",
            password="StrongPassword123!",
            user_type="citizen",
        )
        self.citizen2 = User.objects.create_user(
            username="citizen2",
            email="citizen2@test.com",
            password="StrongPassword123!",
            user_type="citizen",
        )
        self.representative = User.objects.create_user(
            username="rep1",
            email="rep1@test.com",
            password="StrongPassword123!",
            user_type="representative",
        )
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@test.com",
            password="StrongPassword123!",
            user_type="admin",
        )

    def test_get_user_statistics(self):
        """اختبار الحصول على إحصائيات المستخدمين"""
        stats = UserService.get_user_statistics()

        self.assertEqual(stats["total_users"], 4)
        self.assertEqual(stats["citizens"], 2)
        self.assertEqual(stats["representatives"], 1)
        self.assertEqual(stats["admins"], 1)
        self.assertIn("verified_users", stats)
        self.assertIn("unverified_users", stats)

    def test_user_creation(self):
        """اختبار إنشاء المستخدمين"""
        self.assertEqual(self.citizen1.email, "citizen1@test.com")
        self.assertEqual(self.citizen1.user_type, "citizen")
        self.assertTrue(self.citizen1.is_active)

    def test_user_statistics_detailed(self):
        """اختبار إحصائيات المستخدمين المفصلة"""
        stats = UserService.get_user_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn("total_users", stats)
        self.assertIn("verified_users", stats)
        self.assertIn("unverified_users", stats)
