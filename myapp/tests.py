from unittest import mock

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Cart, CartItem, Mahsulot, Order, Wishlist
from .mail import MailError
from .sms import SMSError, is_uz_phone, normalize_phone


def make_product(nomi="Olma", narxi=10000, miqdori=5):
    return Mahsulot.objects.create(nomi=nomi, narxi=narxi, miqdori=miqdori)


class ProductModelTests(TestCase):
    def test_slug_is_generated_and_unique(self):
        a = make_product("Olma")
        b = make_product("Olma")
        self.assertEqual(a.slug, "olma")
        self.assertNotEqual(a.slug, b.slug)
        self.assertTrue(b.slug.startswith("olma-"))


class AuthTests(TestCase):
    def test_register_logs_user_in(self):
        resp = self.client.post(
            reverse("register"),
            {"username": "ali", "password": "Zx9!kLm2pQw"},
        )
        self.assertRedirects(resp, reverse("index"))
        self.assertTrue(User.objects.filter(username="ali").exists())

    def test_index_requires_login(self):
        resp = self.client.get(reverse("index"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(reverse("login"), resp.url)

    def test_login_wrong_password(self):
        User.objects.create_user("ali", password="Zx9!kLm2pQw")
        resp = self.client.post(reverse("login"), {"username": "ali", "password": "bad"})
        self.assertEqual(resp.status_code, 200)

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)


class WishlistTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali", password="pw-Test-123")
        self.client.force_login(self.user)
        self.product = make_product()

    def test_toggle_adds_then_removes(self):
        url = reverse("toggle_wishlist", args=[self.product.id])
        hdr = {"HTTP_X_REQUESTED_WITH": "XMLHttpRequest"}
        self.assertTrue(self.client.post(url, **hdr).json()["added"])
        self.assertEqual(Wishlist.objects.count(), 1)
        self.assertFalse(self.client.post(url, **hdr).json()["added"])
        self.assertEqual(Wishlist.objects.count(), 0)


class CartTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ali", password="pw-Test-123")
        self.product = make_product(miqdori=2)

    def add(self):
        return self.client.post(reverse("add_to_cart", args=[self.product.slug]))

    def test_add_requires_post(self):
        resp = self.client.get(reverse("add_to_cart", args=[self.product.slug]))
        self.assertEqual(resp.status_code, 405)

    def test_add_increments_and_respects_stock(self):
        self.client.force_login(self.user)
        self.add()
        self.add()
        self.add()  # omborda faqat 2 ta
        item = CartItem.objects.get()
        self.assertEqual(item.quantity, 2)

    def test_out_of_stock_cannot_be_added(self):
        self.product.miqdori = 0
        self.product.save()
        self.client.force_login(self.user)
        self.add()
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cart_page_renders_totals(self):
        self.client.force_login(self.user)
        self.add()
        resp = self.client.get(reverse("cart"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["subtotal"], 10000)
        self.assertEqual(resp.context["total"], 10000)

    def test_update_and_remove(self):
        self.client.force_login(self.user)
        self.add()
        item = CartItem.objects.get()
        self.client.post(reverse("cart_update", args=[item.id, "inc"]))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
        self.client.post(reverse("cart_update", args=[item.id, "dec"]))
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.client.post(reverse("cart_update", args=[item.id, "dec"]))  # 1 dan kam -> o'chadi
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_touch_other_users_item(self):
        other = User.objects.create_user("vali", password="pw-Test-123")
        cart = Cart.objects.create(user=other)
        item = CartItem.objects.create(cart=cart, mahsulot=self.product)
        self.client.force_login(self.user)
        resp = self.client.post(reverse("cart_remove", args=[item.id]))
        self.assertEqual(resp.status_code, 404)
        self.assertTrue(CartItem.objects.filter(id=item.id).exists())

    def test_guest_cart_is_merged_on_login(self):
        self.add()  # mehmon sifatida
        self.assertEqual(CartItem.objects.count(), 1)
        self.client.post(
            reverse("login"), {"username": "ali", "password": "pw-Test-123"}
        )
        resp = self.client.get(reverse("cart"))
        self.assertEqual(len(resp.context["cart_items"]), 1)
        self.assertEqual(Cart.objects.filter(user=self.user).count(), 1)

    def test_navbar_count_context(self):
        self.client.force_login(self.user)
        self.add()
        self.add()
        resp = self.client.get(reverse("cart"))
        self.assertEqual(resp.context["cart_count"], 2)


class SMSHelpersTests(TestCase):
    def test_normalize_phone(self):
        self.assertEqual(normalize_phone("+998 90 123-45-67"), "998901234567")
        self.assertEqual(normalize_phone("901234567"), "998901234567")

    def test_is_uz_phone(self):
        self.assertTrue(is_uz_phone("998901234567"))
        self.assertFalse(is_uz_phone("79001234567"))
        self.assertFalse(is_uz_phone("99890"))


@override_settings(SMS_BACKEND="console")
class CheckoutTests(TestCase):
    DATA = {
        "ism": "Ali Valiyev",
        "telefon": "+998 90 123 45 67",
        "manzil": "Toshkent, Chilonzor 5",
        "izoh": "",
    }
    CODE = "123456"

    def setUp(self):
        self.user = User.objects.create_user("ali", password="pw-Test-123")
        self.client.force_login(self.user)
        self.product = make_product(narxi=15000, miqdori=5)
        patcher = mock.patch("myapp.views.generate_code", return_value=self.CODE)
        patcher.start()
        self.addCleanup(patcher.stop)
        sms = mock.patch("myapp.views.send_sms")
        self.send_sms = sms.start()
        self.addCleanup(sms.stop)

    def fill_cart(self, qty=2):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, mahsulot=self.product, quantity=qty)

    def start(self, **extra):
        return self.client.post(reverse("checkout"), {**self.DATA, **extra})

    def verify(self, code):
        return self.client.post(reverse("checkout_verify"), {"code": code})

    def test_empty_cart_redirects(self):
        self.assertRedirects(self.client.get(reverse("checkout")), reverse("cart"))

    def test_step1_sends_sms_and_does_not_create_order(self):
        self.fill_cart()
        resp = self.start()
        self.assertRedirects(resp, reverse("checkout_verify"))
        self.send_sms.assert_called_once()
        phone, text = self.send_sms.call_args[0]
        self.assertEqual(phone, "998901234567")
        self.assertIn(self.CODE, text)
        self.assertEqual(Order.objects.count(), 0)

    def test_correct_code_creates_order_and_reduces_stock(self):
        self.fill_cart(2)
        self.start()
        resp = self.verify(self.CODE)
        order = Order.objects.get()
        self.assertRedirects(resp, reverse("order_detail", args=[order.pk]))
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_price, 30000)
        self.assertEqual(order.items.get().narxi, 15000)
        self.product.refresh_from_db()
        self.assertEqual(self.product.miqdori, 3)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_wrong_code_shows_error_and_creates_nothing(self):
        self.fill_cart()
        self.start()
        resp = self.verify("000000")
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Kod noto")
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_correct_code_works_after_a_wrong_attempt(self):
        self.fill_cart()
        self.start()
        self.verify("000000")
        self.verify(self.CODE)
        self.assertEqual(Order.objects.count(), 1)

    def test_too_many_wrong_attempts_block_even_correct_code(self):
        self.fill_cart()
        self.start()
        for _ in range(5):
            self.verify("000000")
        resp = self.verify(self.CODE)
        self.assertContains(resp, "Urinishlar tugadi")
        self.assertEqual(Order.objects.count(), 0)

    def test_expired_code_is_rejected(self):
        self.fill_cart()
        self.start()
        session = self.client.session
        session["checkout_otp"]["expires"] = 0
        session.save()
        resp = self.verify(self.CODE)
        self.assertContains(resp, "muddati tugadi")
        self.assertEqual(Order.objects.count(), 0)

    def test_code_is_also_emailed(self):
        self.fill_cart()
        self.start(email="Ali@Example.com")
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["ali@example.com"])
        self.assertIn(self.CODE, mail.outbox[0].body)
        self.send_sms.assert_called_once()

    def test_no_email_means_no_mail_sent(self):
        self.fill_cart()
        self.start()
        self.assertEqual(len(mail.outbox), 0)

    def test_code_from_email_creates_order_and_saves_email(self):
        self.fill_cart()
        self.start(email="ali@example.com")
        self.verify(self.CODE)
        self.assertEqual(Order.objects.get().email, "ali@example.com")

    def test_invalid_email_is_rejected(self):
        self.fill_cart()
        resp = self.start(email="not-an-email")
        self.assertEqual(resp.status_code, 200)
        self.send_sms.assert_not_called()

    def test_sms_failure_but_email_ok_still_proceeds(self):
        self.fill_cart()
        self.send_sms.side_effect = SMSError("fail")
        resp = self.start(email="ali@example.com")
        self.assertRedirects(resp, reverse("checkout_verify"))
        self.assertEqual(len(mail.outbox), 1)

    def test_all_channels_failing_stays_on_form(self):
        self.fill_cart()
        self.send_sms.side_effect = SMSError("fail")
        with mock.patch("myapp.views.send_code_email", side_effect=MailError("x")):
            resp = self.start(email="ali@example.com")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Order.objects.count(), 0)

    def test_verify_without_step1_redirects_to_checkout(self):
        self.fill_cart()
        self.assertRedirects(self.verify(self.CODE), reverse("checkout"))

    def test_resend_has_cooldown(self):
        self.fill_cart()
        self.start()
        self.client.post(reverse("resend_code"))
        self.assertEqual(self.send_sms.call_count, 1)  # 60 soniya o'tmagan
        session = self.client.session
        session["checkout_otp"]["sent_at"] = 0
        session.save()
        self.client.post(reverse("resend_code"))
        self.assertEqual(self.send_sms.call_count, 2)

    def test_invalid_phone_is_rejected(self):
        self.fill_cart()
        for bad in ("abc", "+7 900 123 45 67", "12345"):
            resp = self.start(telefon=bad)
            self.assertEqual(resp.status_code, 200)
        self.send_sms.assert_not_called()

    def test_insufficient_stock_blocks_order(self):
        self.fill_cart(3)
        self.start()
        Mahsulot.objects.filter(pk=self.product.pk).update(miqdori=1)
        resp = self.verify(self.CODE)
        self.assertRedirects(resp, reverse("cart"))
        self.assertEqual(Order.objects.count(), 0)

    def place_order(self, qty=2):
        self.fill_cart(qty)
        self.start()
        self.verify(self.CODE)
        return Order.objects.get()

    def test_cancel_restores_stock(self):
        order = self.place_order()
        self.client.post(reverse("order_cancel", args=[order.pk]))
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(order.status, Order.Status.CANCELLED)
        self.assertEqual(self.product.miqdori, 5)

    def test_cancel_twice_does_not_double_restore(self):
        order = self.place_order()
        self.client.post(reverse("order_cancel", args=[order.pk]))
        self.client.post(reverse("order_cancel", args=[order.pk]))
        self.product.refresh_from_db()
        self.assertEqual(self.product.miqdori, 5)

    def test_orders_are_private(self):
        order = self.place_order(1)
        other = User.objects.create_user("vali", password="pw-Test-123")
        self.client.force_login(other)
        self.assertEqual(
            self.client.get(reverse("order_detail", args=[order.pk])).status_code, 404
        )
        self.assertEqual(len(self.client.get(reverse("orders")).context["orders"]), 0)
