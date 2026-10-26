"""SMS yuborish: "console" (test) va "eskiz" (Eskiz.uz) backend'lari."""
import json
import logging
import re
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

ESKIZ_BASE = "https://notify.eskiz.uz/api"
_eskiz_token = None


class SMSError(Exception):
    """SMS yuborib bo'lmaganda ko'tariladi."""


def normalize_phone(raw):
    """'+998 90 123-45-67' -> '998901234567'."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 9:
        digits = "998" + digits
    return digits


def is_uz_phone(phone):
    return bool(re.fullmatch(r"998\d{9}", phone))


def _post(url, fields, token=None):
    data = urllib.parse.urlencode(fields).encode()
    request = urllib.request.Request(url, data=data, method="POST")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode())


def _eskiz_login():
    global _eskiz_token
    result = _post(
        f"{ESKIZ_BASE}/auth/login",
        {"email": settings.ESKIZ_EMAIL, "password": settings.ESKIZ_PASSWORD},
    )
    _eskiz_token = result["data"]["token"]


def _send_eskiz(phone, text):
    if not (settings.ESKIZ_EMAIL and settings.ESKIZ_PASSWORD):
        raise SMSError("SMS xizmati sozlanmagan.")
    for attempt in (1, 2):
        try:
            if _eskiz_token is None or attempt == 2:
                _eskiz_login()
            _post(
                f"{ESKIZ_BASE}/message/sms/send",
                {"mobile_phone": phone, "message": text, "from": settings.ESKIZ_FROM},
                token=_eskiz_token,
            )
            return
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and attempt == 1:
                continue  # token eskirgan: qayta login qilamiz
            logger.error("Eskiz HTTP xatosi: %s", exc.code)
            raise SMSError("SMS yuborib bo'lmadi. Keyinroq urinib ko'ring.") from exc
        except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as exc:
            logger.error("Eskiz xatosi: %s", exc)
            raise SMSError("SMS yuborib bo'lmadi. Keyinroq urinib ko'ring.") from exc


def send_sms(phone, text):
    backend = settings.SMS_BACKEND
    if backend == "console":
        # Terminalga chiqadi (runserver ishlayotgan oynada)
        print(f"\n[SMS -> +{phone}] {text}\n", flush=True)
        return
    if backend == "eskiz":
        _send_eskiz(phone, text)
        return
    raise SMSError(f"Noma'lum SMS backend: {backend}")
