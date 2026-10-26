"""Tasdiqlash kodini emailga yuborish."""
import logging
import smtplib

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class MailError(Exception):
    """Email yuborib bo'lmaganda ko'tariladi."""


def send_code_email(to_email, code):
    try:
        send_mail(
            subject="MyShop: tasdiqlash kodi",
            message=(
                f"Sizning tasdiqlash kodingiz: {code}\n\n"
                "Kod 5 daqiqa amal qiladi. Uni hech kimga bermang.\n"
                "Agar buyurtmani siz bermagan bo'lsangiz, bu xatni e'tiborsiz qoldiring."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
    except (smtplib.SMTPException, OSError) as exc:
        logger.error("Email yuborilmadi: %s", exc)
        raise MailError("Email yuborib bo'lmadi.") from exc
