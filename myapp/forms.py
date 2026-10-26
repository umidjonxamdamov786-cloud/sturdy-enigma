import re

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

from .models import Order, Review
from .sms import is_uz_phone, normalize_phone


class RegisterForm(forms.Form):
    username = forms.CharField(
        label="Username",
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "login",
                "placeholder": "Username kiriting",
                "autocomplete": "username",
            }
        ),
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        widget=forms.EmailInput(
            attrs={
                "class": "login",
                "placeholder": "Email (ixtiyoriy)",
                "autocomplete": "email",
            }
        ),
    )
    password = forms.CharField(
        label="Parol",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "login",
                "placeholder": "Kamida 8 ta belgi",
                "autocomplete": "new-password",
            }
        ),
    )

    def clean_username(self):
        username = self.cleaned_data.get("username", "").strip()
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Bunday username allaqachon mavjud!")
        return username

    def clean_password(self):
        password = self.cleaned_data.get("password")
        # Username/email ga o'xshash parolni ham tekshirish uchun vaqtinchalik user
        user = User(
            username=self.cleaned_data.get("username", ""),
            email=self.cleaned_data.get("email", ""),
        )
        validate_password(password, user=user)
        return password


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "comment"]
        widgets = {
            "rating": forms.Select(attrs={"class": "form-control"}),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Mahsulot haqida fikringiz?",
                }
            ),
        }


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ["ism", "telefon", "email", "manzil", "izoh"]
        widgets = {
            "ism": forms.TextInput(attrs={"placeholder": "Ismingiz", "autocomplete": "name"}),
            "telefon": forms.TextInput(attrs={"placeholder": "+998 90 123 45 67", "autocomplete": "tel", "inputmode": "tel"}),
            "email": forms.EmailInput(attrs={"placeholder": "Email (kod shu yerga ham yuboriladi)", "autocomplete": "email"}),
            "manzil": forms.Textarea(attrs={"rows": 3, "placeholder": "Shahar, ko'cha, uy", "autocomplete": "street-address"}),
            "izoh": forms.Textarea(attrs={"rows": 2, "placeholder": "Qo'shimcha izoh (ixtiyoriy)"}),
        }

    def clean_ism(self):
        ism = self.cleaned_data["ism"].strip()
        if len(ism) < 2:
            raise forms.ValidationError("Ismni to'liq kiriting.")
        return ism

    def clean_telefon(self):
        telefon = self.cleaned_data["telefon"].strip()
        if not re.fullmatch(r"\+?[\d\s\-()]+", telefon) or not is_uz_phone(normalize_phone(telefon)):
            raise forms.ValidationError(
                "Telefon raqamini to'g'ri kiriting (masalan: +998 90 123 45 67)."
            )
        return telefon

    def clean_email(self):
        return self.cleaned_data.get("email", "").strip().lower()

    def clean_manzil(self):
        manzil = self.cleaned_data["manzil"].strip()
        if len(manzil) < 5:
            raise forms.ValidationError("Manzilni to'liqroq yozing.")
        return manzil
