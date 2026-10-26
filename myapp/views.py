import hmac
import secrets
import time
from hashlib import sha256

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CheckoutForm, RegisterForm, ReviewForm
from .mail import MailError, send_code_email
from .sms import SMSError, normalize_phone, send_sms
from .models import (
    Cart,
    CartItem,
    Category,
    Mahsulot,
    Order,
    OrderItem,
    Review,
    Wishlist,
)


def _product_queryset():
    """Umumiy mahsulot queryset (optimallashtirilgan)."""
    return (
        Mahsulot.objects.select_related("category")
        .annotate(
            avg_rating=Avg("reviews__rating"),
            review_count=Count("reviews", distinct=True),
            wishlist_count=Count("wishlisted_by", distinct=True),
        )
        .order_by("-id")
    )


@login_required(login_url="login")
def index(request):
    mahsulotlar = _product_queryset()
    categories = Category.objects.all()

    category_id = request.GET.get("category", "").strip()
    q = request.GET.get("q", "").strip()

    if category_id.isdigit():
        mahsulotlar = mahsulotlar.filter(category_id=int(category_id))
    if q:
        mahsulotlar = mahsulotlar.filter(nomi__icontains=q)

    paginator = Paginator(mahsulotlar, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    wishlist_ids = set(
        Wishlist.objects.filter(user=request.user).values_list("mahsulot_id", flat=True)
    )

    return render(
        request,
        "index.html",
        {
            "mahsulotlar": page_obj,
            "page_obj": page_obj,
            "wishlist_ids": wishlist_ids,
            "category": categories,
            "q": q,
            "selected_category": int(category_id) if category_id.isdigit() else None,
        },
    )


def _safe_next(request):
    """?next= parametrini xavfsiz tekshirib qaytaradi."""
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return ""


def login_form(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Tizimga muvaffaqiyatli kirdingiz!")
            return redirect(_safe_next(request) or "index")
        messages.error(request, "Login yoki parol xato!")
    return render(request, "login.html", {"next": _safe_next(request)})


def register_view(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email") or "",
                password=form.cleaned_data["password"],
            )
            login(request, user)
            messages.success(request, "Muvaffaqiyatli ro'yxatdan o'tdingiz!")
            return redirect("index")
    else:
        form = RegisterForm()
    return render(request, "register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Siz tizimdan chiqdingiz!")
    return redirect("login")


@login_required(login_url="login")
def product_view(request, slug):
    mahsulot = get_object_or_404(
        Mahsulot.objects.select_related("category").prefetch_related("images"),
        slug=slug,
    )
    reviews = mahsulot.reviews.select_related("user").order_by("-created")

    if request.method == "POST":
        form = ReviewForm(request.POST)
        if form.is_valid():
            Review.objects.update_or_create(
                mahsulot=mahsulot,
                user=request.user,
                defaults={
                    "rating": form.cleaned_data["rating"],
                    "comment": form.cleaned_data["comment"],
                },
            )
            messages.success(request, "Sharhingiz uchun rahmat!")
            return redirect("products-view", slug=mahsulot.slug)
    else:
        form = ReviewForm()
       
        korilganlar = request.session.get("korilgan", [])
        if mahsulot.id not in korilganlar:
            Mahsulot.objects.filter(id=mahsulot.id).update(korish=F("korish") + 1)
            korilganlar.append(mahsulot.id)
            request.session["korilgan"] = korilganlar
            mahsulot.refresh_from_db()

    stats = reviews.aggregate(avg=Avg("rating"), total=Count("id"))
    context = {
        "mahsulot": mahsulot,
        "in_wishlist": Wishlist.objects.filter(
            user=request.user, mahsulot=mahsulot
        ).exists(),
        "wishlist_count": mahsulot.wishlisted_by.count(),
        "reviews": reviews,
        "average_rating": round(stats["avg"] or 0, 1),
        "review_count": stats["total"] or 0,
        "form": form,
    }
    return render(request, "product.html", context)



@login_required(login_url="login")
def wishlist_list(request):
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related("mahsulot")
    return render(request, "wishlist.html", {"wishlist_items": wishlist_items})



@login_required(login_url="login")
@require_POST
def toggle_wishlist(request, product_id):
    mahsulot = get_object_or_404(Mahsulot, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user, mahsulot=mahsulot
    )

    if not created:
        
        wishlist_item.delete()
        added = False
    else:
        added = True

    
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(
            {
                "added": added,
                "count": mahsulot.wishlisted_by.count(),
                "total": Wishlist.objects.filter(user=request.user).count(),
            }
        )

    
    next_url = request.META.get("HTTP_REFERER", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(next_url)
    return redirect("wishlist_list")


# ---------------------------------------------------------------------------
# Savatcha
# ---------------------------------------------------------------------------

def _merge_guest_cart(request, cart):
    """Mehmon savatchasini kirgan foydalanuvchi savatchasiga qo'shadi."""
    guest_id = request.session.pop("cart_id", None)
    if not guest_id:
        return
    guest = Cart.objects.filter(id=guest_id, user=None).first()
    if not guest:
        return
    for item in guest.items.select_related("mahsulot"):
        mine, created = CartItem.objects.get_or_create(
            cart=cart, mahsulot=item.mahsulot, defaults={"quantity": item.quantity}
        )
        if not created:
            mine.quantity = min(mine.quantity + item.quantity, max(item.mahsulot.miqdori, 1))
            mine.save(update_fields=["quantity"])
    guest.delete()


def cart_qism(request):
    """Joriy foydalanuvchi (yoki mehmon) savatchasini qaytaradi."""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).order_by("id").first()
        if cart is None:
            cart = Cart.objects.create(user=request.user)
        _merge_guest_cart(request, cart)
        return cart

    cart = None
    cart_id = request.session.get("cart_id")
    if cart_id:
        cart = Cart.objects.filter(id=cart_id, user=None).first()
    if cart is None:
        cart = Cart.objects.create()
        request.session["cart_id"] = cart.id
    return cart


def _redirect_back(request, fallback="index"):
    """Foydalanuvchini oldingi (xavfsiz) sahifaga qaytaradi."""
    ref = request.META.get("HTTP_REFERER", "")
    if ref and url_has_allowed_host_and_scheme(
        ref,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return redirect(ref)
    return redirect(fallback)


@require_POST
def add_to_cart(request, slug):
    mahsulot = get_object_or_404(Mahsulot, slug=slug)

    if mahsulot.miqdori < 1:
        messages.error(request, "Bu mahsulot omborda qolmagan.")
        return _redirect_back(request)

    cart = cart_qism(request)
    item, created = CartItem.objects.get_or_create(cart=cart, mahsulot=mahsulot)

    if created:
        messages.success(request, "Savatchaga qo'shildi.")
    elif item.quantity >= mahsulot.miqdori:
        messages.warning(request, "Omborda bundan ortiq mahsulot yo'q.")
    else:
        item.quantity += 1
        item.save(update_fields=["quantity"])
        messages.success(request, "Savatchaga qo'shildi.")
    return _redirect_back(request)


def cart_detail(request):
    cart = cart_qism(request)
    cart_items = list(cart.items.select_related("mahsulot", "mahsulot__category"))
    subtotal = sum(item.total_price for item in cart_items)
    discount = 0
    return render(
        request,
        "cart.html",
        {
            "cart": cart,
            "cart_items": cart_items,
            "subtotal": subtotal,
            "discount": discount,
            "total": subtotal - discount,
        },
    )


@require_POST
def update_cart_item(request, item_id, action):
    cart = cart_qism(request)
    item = get_object_or_404(
        CartItem.objects.select_related("mahsulot"), id=item_id, cart=cart
    )
    if action == "inc":
        if item.quantity < item.mahsulot.miqdori:
            item.quantity += 1
            item.save(update_fields=["quantity"])
        else:
            messages.warning(request, "Omborda bundan ortiq mahsulot yo'q.")
    elif action == "dec":
        if item.quantity > 1:
            item.quantity -= 1
            item.save(update_fields=["quantity"])
        else:
            item.delete()
    else:
        return redirect("cart")
    return redirect("cart")


@require_POST
def remove_cart_item(request, item_id):
    cart = cart_qism(request)
    get_object_or_404(CartItem, id=item_id, cart=cart).delete()
    messages.success(request, "Mahsulot savatchadan o'chirildi.")
    return redirect("cart")




class StockError(Exception):
    """Ombordagi miqdor buyurtma uchun yetmaganda ko'tariladi."""

    def __init__(self, mahsulot):
        super().__init__(mahsulot.nomi)
        self.mahsulot = mahsulot


class EmptyCartError(Exception):
    """Buyurtma paytida savatcha bo'sh bo'lib qolganda."""


OTP_KEY = "checkout_otp"


def generate_code():
    return f"{secrets.randbelow(10**6):06d}"


def _code_hash(phone, code):
    return hmac.new(
        settings.SECRET_KEY.encode(), f"{phone}:{code}".encode(), sha256
    ).hexdigest()


def _mask_phone(phone):
    if len(phone) == 12:
        return f"+{phone[:3]} ** *** {phone[8:10]} {phone[10:]}"
    return f"+{phone}"


def _mask_email(email):
    name, _, domain = email.partition("@")
    return f"{name[:1]}***@{domain}"


def _send_code(request, state):
    """Kodni SMS (va email kiritilgan bo'lsa email) orqali yuboradi."""
    code = generate_code()
    targets = []

    try:
        send_sms(
            state["phone"],
            f"MyShop: tasdiqlash kodi {code}. Uni hech kimga bermang.",
        )
        targets.append(_mask_phone(state["phone"]))
    except SMSError:
        pass

    email = state["data"].get("email")
    if email:
        try:
            send_code_email(email, code)
            targets.append(_mask_email(email))
        except MailError:
            pass

    if not targets:
        raise SMSError("Kodni yuborib bo'lmadi. Keyinroq urinib ko'ring.")

    now = time.time()
    state.update(
        hash=_code_hash(state["phone"], code),
        expires=now + settings.OTP_TTL,
        sent_at=now,
        attempts=0,
        sends=state.get("sends", 0) + 1,
        targets=targets,
    )
    request.session[OTP_KEY] = state


def _create_order(user, cart, data):
    """Buyurtmani yaratadi, ombor miqdorini kamaytiradi, savatchani tozalaydi."""
    with transaction.atomic():
        items = list(cart.items.select_related("mahsulot"))
        if not items:
            raise EmptyCartError()
        products = {
            p.id: p
            for p in Mahsulot.objects.select_for_update().filter(
                id__in=[i.mahsulot_id for i in items]
            )
        }
        for item in items:
            if products[item.mahsulot_id].miqdori < item.quantity:
                raise StockError(item.mahsulot)

        order = Order.objects.create(user=user, **data)
        for item in items:
            product = products[item.mahsulot_id]
            OrderItem.objects.create(
                order=order,
                mahsulot=product,
                nomi=product.nomi,
                narxi=product.narxi,
                quantity=item.quantity,
            )
            product.miqdori -= item.quantity
            product.save(update_fields=["miqdori"])
        cart.items.all().delete()
    return order


@login_required(login_url="login")
def checkout(request):
    """1-qadam: ma'lumotlarni kiritish va SMS kod yuborish."""
    cart = cart_qism(request)
    cart_items = list(cart.items.select_related("mahsulot"))
    if not cart_items:
        messages.warning(request, "Savatchangiz bo'sh.")
        return redirect("cart")

    saved = request.session.get(OTP_KEY, {})
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            data = {
                key: form.cleaned_data[key]
                for key in ("ism", "telefon", "email", "manzil", "izoh")
            }
            phone = normalize_phone(data["telefon"])
            # Raqam o'zgarmagan bo'lsa SMS yuborishlar sonini saqlab qolamiz
            sends = saved.get("sends", 0) if saved.get("phone") == phone else 0
            if sends >= settings.OTP_MAX_SENDS:
                messages.error(request, "SMS limiti tugadi. Keyinroq urinib ko'ring.")
            else:
                state = {"data": data, "phone": phone, "sends": sends}
                try:
                    _send_code(request, state)
                except SMSError as exc:
                    messages.error(request, str(exc))
                else:
                    return redirect("checkout_verify")
    else:
        initial = saved.get("data") or {
            "ism": request.user.get_full_name() or request.user.username
        }
        form = CheckoutForm(initial=initial)

    subtotal = sum(i.total_price for i in cart_items)
    return render(
        request,
        "checkout.html",
        {"form": form, "cart_items": cart_items, "total": subtotal},
    )


@login_required(login_url="login")
def checkout_verify(request):
    """2-qadam: SMS kodni tekshirish. Kod to'g'ri bo'lsa buyurtma beriladi."""
    state = request.session.get(OTP_KEY)
    if not state or "hash" not in state:
        return redirect("checkout")

    cart = cart_qism(request)
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        if time.time() > state["expires"]:
            messages.error(request, "Kod muddati tugadi. Yangi kod so'rang.")
        elif state["attempts"] >= settings.OTP_MAX_ATTEMPTS:
            messages.error(request, "Urinishlar tugadi. Yangi kod so'rang.")
        else:
            state["attempts"] += 1
            request.session[OTP_KEY] = state
            if hmac.compare_digest(_code_hash(state["phone"], code), state["hash"]):
                try:
                    order = _create_order(request.user, cart, state["data"])
                except EmptyCartError:
                    request.session.pop(OTP_KEY, None)
                    messages.warning(request, "Savatchangiz bo'sh.")
                    return redirect("cart")
                except StockError as exc:
                    request.session.pop(OTP_KEY, None)
                    messages.error(
                        request,
                        f"“{exc.mahsulot.nomi}” omborda yetarli emas. Savatchani yangilang.",
                    )
                    return redirect("cart")
                request.session.pop(OTP_KEY, None)
                messages.success(request, "Telefon tasdiqlandi. Buyurtmangiz qabul qilindi!")
                return redirect("order_detail", pk=order.pk)
            left = settings.OTP_MAX_ATTEMPTS - state["attempts"]
            messages.error(request, f"Kod noto'g'ri. Qolgan urinishlar: {left}")

    resend_in = max(0, int(settings.OTP_RESEND_COOLDOWN - (time.time() - state["sent_at"])))
    return render(
        request,
        "checkout_verify.html",
        {
            "targets": state.get("targets") or [_mask_phone(state["phone"])],
            "resend_in": resend_in,
            "console_mode": settings.SMS_BACKEND == "console"
            or settings.EMAIL_BACKEND.endswith("console.EmailBackend"),
        },
    )


@login_required(login_url="login")
@require_POST
def resend_code(request):
    state = request.session.get(OTP_KEY)
    if not state or "hash" not in state:
        return redirect("checkout")
    wait = settings.OTP_RESEND_COOLDOWN - (time.time() - state["sent_at"])
    if wait > 0:
        messages.error(request, f"Yangi kodni {int(wait) + 1} soniyadan keyin so'rang.")
    elif state["sends"] >= settings.OTP_MAX_SENDS:
        messages.error(request, "SMS limiti tugadi. Keyinroq urinib ko'ring.")
    else:
        try:
            _send_code(request, state)
            messages.success(request, "Yangi kod yuborildi.")
        except SMSError as exc:
            messages.error(request, str(exc))
    return redirect("checkout_verify")


@login_required(login_url="login")
def orders_list(request):
    orders = Order.objects.filter(user=request.user).prefetch_related("items")
    return render(request, "orders.html", {"orders": orders})


@login_required(login_url="login")
def order_detail(request, pk):
    order = get_object_or_404(
        Order.objects.prefetch_related("items"), pk=pk, user=request.user
    )
    return render(request, "order_detail.html", {"order": order})


@login_required(login_url="login")
@require_POST
def cancel_order(request, pk):
    with transaction.atomic():
        order = get_object_or_404(
            Order.objects.select_for_update(), pk=pk, user=request.user
        )
        if order.status != Order.Status.NEW:
            messages.error(request, "Bu buyurtmani endi bekor qilib bo'lmaydi.")
            return redirect("order_detail", pk=order.pk)
        for item in order.items.select_related("mahsulot"):
            if item.mahsulot_id:
                Mahsulot.objects.filter(pk=item.mahsulot_id).update(
                    miqdori=F("miqdori") + item.quantity
                )
        order.status = Order.Status.CANCELLED
        order.save(update_fields=["status"])
    messages.success(request, "Buyurtma bekor qilindi.")
    return redirect("order_detail", pk=order.pk)
