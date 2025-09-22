# tests_models.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import RefreshToken, PasswordResetToken, EmailVerificationToken

User = get_user_model()

class UserModelTest(TestCase):
    """
    اختبارات نموذج المستخدم
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
            first_name="Test",
            last_name="User",
            user_type="citizen"
        )

    def test_user_creation(self):
        """ اختبار إنشاء مستخدم جديد """
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("password123"))
        self.assertEqual(self.user.user_type, "citizen")

    def test_full_name_property(self):
        """ اختبار خاصية full_name """
        self.assertEqual(self.user.full_name, "Test User")

    def test_user_type_properties(self):
        """ اختبار خصائص نوع المستخدم """
        self.assertTrue(self.user.is_citizen())
        self.assertFalse(self.user.is_representative())
        self.assertFalse(self.user.is_admin_user())

class TokenModelsTest(TestCase):
    """
    اختبارات نماذج الرموز
    """

    def setUp(self):
        self.user = User.objects.create_user(
            username="tokenuser",
            email="token@example.com",
            password="password123"
        )

    def test_refresh_token_model(self):
        """ اختبار نموذج RefreshToken """
        expires_at = timezone.now() + timedelta(days=1)
        refresh_token = RefreshToken.objects.create(
            user=self.user,
            token="testrefreshtoken",
            expires_at=expires_at
        )
        self.assertFalse(refresh_token.is_expired())
        self.assertFalse(refresh_token.is_revoked)

        refresh_token.revoke()
        self.assertTrue(refresh_token.is_revoked)

    def test_password_reset_token_model(self):
        """ اختبار نموذج PasswordResetToken """
        expires_at = timezone.now() + timedelta(hours=1)
        reset_token = PasswordResetToken.objects.create(
            user=self.user,
            expires_at=expires_at
        )
        self.assertTrue(reset_token.is_valid())
        self.assertFalse(reset_token.is_expired())
        self.assertFalse(reset_token.is_used)

        reset_token.is_used = True
        reset_token.save()
        self.assertFalse(reset_token.is_valid())

    def test_email_verification_token_model(self):
        """ اختبار نموذج EmailVerificationToken """
        expires_at = timezone.now() + timedelta(hours=1)
        verification_token = EmailVerificationToken.objects.create(
            user=self.user,
            expires_at=expires_at
        )
        self.assertTrue(verification_token.is_valid())
        self.assertFalse(verification_token.is_expired())
        self.assertFalse(verification_token.is_used)

        verification_token.is_used = True
        verification_token.save()
        self.assertFalse(verification_token.is_valid())

