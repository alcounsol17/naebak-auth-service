"""
خدمة إدارة الأسرار باستخدام Google Secret Manager
"""

import logging
import os
from typing import Optional

from google.api_core import exceptions
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    مدير الأسرار باستخدام Google Secret Manager
    """

    def __init__(self, project_id: Optional[str] = None):
        """
        تهيئة مدير الأسرار

        Args:
            project_id: معرف مشروع Google Cloud
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.client = None

        if self.project_id:
            try:
                self.client = secretmanager.SecretManagerServiceClient()
                logger.info(f"تم تهيئة Secret Manager للمشروع: {self.project_id}")
            except Exception as e:
                logger.warning(f"فشل في تهيئة Secret Manager: {e}")
                self.client = None
        else:
            logger.warning(
                "لم يتم تحديد GOOGLE_CLOUD_PROJECT، سيتم استخدام متغيرات البيئة المحلية"
            )

    def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """
        جلب سر من Google Secret Manager

        Args:
            secret_name: اسم السر
            version: إصدار السر (افتراضي: latest)

        Returns:
            قيمة السر أو None في حالة الفشل
        """
        if not self.client or not self.project_id:
            # العودة إلى متغيرات البيئة المحلية
            return os.getenv(secret_name)

        try:
            name = (
                f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            )
            response = self.client.access_secret_version(request={"name": name})
            secret_value = response.payload.data.decode("UTF-8")
            logger.info(f"تم جلب السر بنجاح: {secret_name}")
            return secret_value

        except exceptions.NotFound:
            logger.warning(f"السر غير موجود: {secret_name}")
            # العودة إلى متغيرات البيئة المحلية
            return os.getenv(secret_name)

        except Exception as e:
            logger.error(f"خطأ في جلب السر {secret_name}: {e}")
            # العودة إلى متغيرات البيئة المحلية
            return os.getenv(secret_name)

    def create_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        إنشاء سر جديد في Google Secret Manager

        Args:
            secret_name: اسم السر
            secret_value: قيمة السر

        Returns:
            True في حالة النجاح، False في حالة الفشل
        """
        if not self.client or not self.project_id:
            logger.warning("Secret Manager غير متاح، لا يمكن إنشاء أسرار جديدة")
            return False

        try:
            parent = f"projects/{self.project_id}"

            # إنشاء السر
            secret = {"replication": {"automatic": {}}}
            response = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": secret,
                }
            )
            logger.info(f"تم إنشاء السر: {response.name}")

            # إضافة قيمة السر
            response = self.client.add_secret_version(
                request={
                    "parent": response.name,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )
            logger.info(f"تم إضافة قيمة السر: {response.name}")
            return True

        except exceptions.AlreadyExists:
            logger.warning(f"السر موجود مسبقاً: {secret_name}")
            return False

        except Exception as e:
            logger.error(f"خطأ في إنشاء السر {secret_name}: {e}")
            return False


# إنشاء مثيل عام لمدير الأسرار
secrets_manager = SecretsManager()


def get_secret(secret_name: str, default: str = None) -> str:
    """
    دالة مساعدة لجلب الأسرار

    Args:
        secret_name: اسم السر
        default: القيمة الافتراضية

    Returns:
        قيمة السر أو القيمة الافتراضية
    """
    secret_value = secrets_manager.get_secret(secret_name)
    return secret_value or default or ""
