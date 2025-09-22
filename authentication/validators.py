"""
مدققات كلمات المرور والبيانات
"""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class StrongPasswordValidator:
    """
    مدقق كلمة المرور القوية
    """

    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        """
        التحقق من قوة كلمة المرور
        """
        errors = []

        # الطول الأدنى
        if len(password) < self.min_length:
            errors.append(f"كلمة المرور يجب أن تكون {self.min_length} أحرف على الأقل")

        # وجود أحرف كبيرة
        if not re.search(r"[A-Z]", password):
            errors.append("كلمة المرور يجب أن تحتوي على حرف كبير واحد على الأقل")

        # وجود أحرف صغيرة
        if not re.search(r"[a-z]", password):
            errors.append("كلمة المرور يجب أن تحتوي على حرف صغير واحد على الأقل")

        # وجود أرقام
        if not re.search(r"\d", password):
            errors.append("كلمة المرور يجب أن تحتوي على رقم واحد على الأقل")

        # وجود رموز خاصة
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("كلمة المرور يجب أن تحتوي على رمز خاص واحد على الأقل")

        # تجنب الكلمات الشائعة
        common_passwords = [
            "password",
            "123456",
            "password123",
            "admin",
            "qwerty",
            "letmein",
            "welcome",
            "monkey",
            "1234567890",
        ]
        if password.lower() in common_passwords:
            errors.append("كلمة المرور ضعيفة جداً، يرجى اختيار كلمة مرور أقوى")

        # تجنب معلومات المستخدم
        if user:
            user_info = [
                user.username.lower() if user.username else "",
                user.email.split("@")[0].lower() if user.email else "",
                user.first_name.lower() if user.first_name else "",
                user.last_name.lower() if user.last_name else "",
            ]

            for info in user_info:
                if info and len(info) > 2 and info in password.lower():
                    errors.append("كلمة المرور لا يجب أن تحتوي على معلومات شخصية")
                    break

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل، "
            "وتشمل أحرف كبيرة وصغيرة وأرقام ورموز خاصة"
        )


class EmailValidator:
    """
    مدقق البريد الإلكتروني المحسن
    """

    @staticmethod
    def validate_email_domain(email):
        """
        التحقق من صحة نطاق البريد الإلكتروني
        """
        # قائمة النطاقات المحظورة
        blocked_domains = [
            "10minutemail.com",
            "tempmail.org",
            "guerrillamail.com",
            "mailinator.com",
        ]

        domain = email.split("@")[1].lower()
        if domain in blocked_domains:
            raise ValidationError("هذا النطاق غير مسموح")

        return True


class NationalIdValidator:
    """
    مدقق الرقم القومي المصري
    """

    @staticmethod
    def validate_egyptian_national_id(national_id):
        """
        التحقق من صحة الرقم القومي المصري
        """
        if not national_id:
            return True  # اختياري

        # يجب أن يكون 14 رقم
        if not re.match(r"^\d{14}$", national_id):
            raise ValidationError("الرقم القومي يجب أن يكون 14 رقم")

        # التحقق من صحة القرن والسنة
        century_digit = int(national_id[0])
        if century_digit not in [2, 3]:  # 2 للقرن العشرين، 3 للقرن الواحد والعشرين
            raise ValidationError("الرقم القومي غير صحيح")

        # التحقق من صحة الشهر
        month = int(national_id[3:5])
        if month < 1 or month > 12:
            raise ValidationError("الرقم القومي غير صحيح - الشهر غير صالح")

        # التحقق من صحة اليوم
        day = int(national_id[5:7])
        if day < 1 or day > 31:
            raise ValidationError("الرقم القومي غير صحيح - اليوم غير صالح")

        return True


class PhoneNumberValidator:
    """
    مدقق رقم الهاتف المصري
    """

    @staticmethod
    def validate_egyptian_phone(phone):
        """
        التحقق من صحة رقم الهاتف المصري
        """
        if not phone:
            return True  # اختياري

        # إزالة المسافات والرموز
        phone = re.sub(r"[^\d+]", "", phone)

        # أنماط الأرقام المصرية المقبولة
        patterns = [
            r"^(\+20|0020|20)?1[0125]\d{8}$",  # موبايل
            r"^(\+20|0020|20)?[23]\d{7}$",  # أرضي
        ]

        for pattern in patterns:
            if re.match(pattern, phone):
                return True

        raise ValidationError("رقم الهاتف غير صحيح")
