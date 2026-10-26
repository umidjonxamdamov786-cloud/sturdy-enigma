from django.db import models
from django.utils.text import slugify
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User


class Category(models.Model):
    """Mahsulot kategoriyasi."""
    nomi = models.CharField("Nomi", max_length=200)

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ["nomi"]
        # Eski jadval nomini saqlaymiz (mavjud ma'lumotlar saqlansin)
        db_table = "myapp_catgeory"

    def __str__(self):
        return self.nomi


class Mahsulot(models.Model):
    """Asosiy mahsulot modeli."""
    nomi = models.CharField("Mahsulot nomi", max_length=200)
    slug = models.SlugField("Slug", unique=True, blank=True, null=True)
    narxi = models.PositiveIntegerField("Narx")
    tavsifi = models.TextField("Tavsif", blank=True)
    image = models.ImageField(
        "Asosiy rasm", upload_to="mahsulotlar/", blank=True, null=True
    )
    miqdori = models.PositiveIntegerField("Ombordagi miqdor", default=0)
    korish = models.PositiveIntegerField("Ko'rishlar soni", default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name="mahsulotlar",
        blank=True,
        null=True,
        verbose_name="Kategoriya",
    )
    created = models.DateTimeField("Yaratilgan", auto_now_add=True, null=True)
    updated = models.DateTimeField("Yangilangan", auto_now=True, null=True)

    class Meta:
        verbose_name = "Mahsulot"
        verbose_name_plural = "Mahsulotlar"
        ordering = ["-id"]

    def __str__(self):
        return self.nomi

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nomi) or "mahsulot"
            candidate = base_slug
            while (
                Mahsulot.objects.filter(slug=candidate)
                .exclude(pk=self.pk)
                .exists()
            ):
                candidate = f"{base_slug}-{get_random_string(5).lower()}"
            self.slug = candidate
        super().save(*args, **kwargs)


class ProductImage(models.Model):
    """Mahsulotning qo'shimcha rasmlari."""
    product = models.ForeignKey(
        Mahsulot,
        on_delete=models.CASCADE,
        related_name="images",
        verbose_name="Mahsulot",
    )
    image = models.ImageField("Rasm", upload_to="products/")

    class Meta:
        verbose_name = "Qo'shimcha rasm"
        verbose_name_plural = "Qo'shimcha rasmlar"

    def __str__(self):
        return f"{self.product.nomi} — rasm {self.pk or ''}"


class Review(models.Model):
    """Mahsulotga foydalanuvchi sharhi va reytingi."""
    mahsulot = models.ForeignKey(
        Mahsulot,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Mahsulot",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Foydalanuvchi",
    )
    rating = models.PositiveSmallIntegerField(
        "Reyting",
        choices=[(i, f"{i} yulduz") for i in range(1, 6)],
        default=5,
    )
    comment = models.TextField("Izoh")
    created = models.DateTimeField("Sana", auto_now_add=True)

    class Meta:
        verbose_name = "Sharh"
        verbose_name_plural = "Sharhlar"
        ordering = ["-created"]
        unique_together = [("mahsulot", "user")]

    def __str__(self):
        return f"{self.user.username} — {self.mahsulot.nomi} ({self.rating}★)"

class Wishlist(models.Model):
    """Foydalanuvchining sevimli mahsulotlari."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="wishlist",
        verbose_name="Foydalanuvchi",
    )
    mahsulot = models.ForeignKey(
        Mahsulot,
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
        verbose_name="Mahsulot",
    )
    created_at = models.DateTimeField("Qo'shilgan", auto_now_add=True)

    class Meta:
        verbose_name = "Sevimli mahsulot"
        verbose_name_plural = "Sevimli mahsulotlar"
        ordering = ["-created_at"]
   
        unique_together = ('user', 'mahsulot')

    def __str__(self):
        return f"{self.user.username} — {self.mahsulot.nomi}"

class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Savat #{self.id} - {self.user.username if self.user else 'Mehmon'}"

    @property
    def total_price(self):
        return sum (item.total_price for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    mahsulot = models.ForeignKey(Mahsulot, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.mahsulot.nomi}"

    @property
    def total_price(self):
        return self.mahsulot.narxi * self.quantity


class Order(models.Model):
    """Foydalanuvchi buyurtmasi."""

    class Status(models.TextChoices):
        NEW = "new", "Yangi"
        PROCESSING = "processing", "Jarayonda"
        DELIVERED = "delivered", "Yetkazildi"
        CANCELLED = "cancelled", "Bekor qilindi"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name="Foydalanuvchi",
    )
    ism = models.CharField("Ism", max_length=150)
    telefon = models.CharField("Telefon", max_length=20)
    email = models.EmailField("Email", blank=True)
    manzil = models.TextField("Manzil")
    izoh = models.TextField("Izoh", blank=True)
    status = models.CharField(
        "Holati", max_length=20, choices=Status.choices, default=Status.NEW
    )
    created = models.DateTimeField("Sana", auto_now_add=True)

    class Meta:
        verbose_name = "Buyurtma"
        verbose_name_plural = "Buyurtmalar"
        ordering = ["-created"]

    def __str__(self):
        return f"Buyurtma #{self.pk} — {self.user.username}"

    @property
    def total_price(self):
        return sum(item.total_price for item in self.items.all())


class OrderItem(models.Model):
    """Buyurtmadagi mahsulot (narx va nom buyurtma paytida saqlanadi)."""

    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="items", verbose_name="Buyurtma"
    )
    mahsulot = models.ForeignKey(
        Mahsulot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Mahsulot",
    )
    nomi = models.CharField("Nomi", max_length=200)
    narxi = models.PositiveIntegerField("Narx")
    quantity = models.PositiveIntegerField("Miqdor", default=1)

    class Meta:
        verbose_name = "Buyurtma mahsuloti"
        verbose_name_plural = "Buyurtma mahsulotlari"

    def __str__(self):
        return f"{self.quantity} x {self.nomi}"

    @property
    def total_price(self):
        return self.narxi * self.quantity
