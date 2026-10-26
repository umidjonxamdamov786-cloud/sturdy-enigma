# MyShop (Django)

```bash
pip install -r requirements.txt
python manage.py migrate        # 0015 (buyurtmalar) migratsiyasini qo'llaydi
python manage.py createsuperuser
python manage.py runserver
python manage.py test           # testlarni ishga tushirish
```

Production: `DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` va `python manage.py collectstatic` kerak.

## SMS tasdiqlash
Buyurtma berishda telefon raqamga 6 xonali kod yuboriladi.

- **Test rejimi** (standart, `SMS_BACKEND=console`): kod `runserver` ishlayotgan terminalda chiqadi.
- **Haqiqiy SMS** (Eskiz.uz): `SMS_BACKEND=eskiz`, `ESKIZ_EMAIL`, `ESKIZ_PASSWORD` (ixtiyoriy `ESKIZ_FROM`) o'rnating.
- Kod 5 daqiqa amal qiladi, 5 ta urinish, qayta yuborish 60 soniyada bir marta.

## Email orqali kod
Buyurtma formasida email kiritilsa, kod SMS bilan birga emailga ham yuboriladi (email ixtiyoriy).

- **Test rejimi:** xat terminalda chiqadi.
- **Haqiqiy email:** `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` (Gmail uchun "App password"), ixtiyoriy `EMAIL_HOST`, `EMAIL_PORT`, `DEFAULT_FROM_EMAIL`.
- Yangi migratsiya: `0016_order_email` (`python manage.py migrate`).
