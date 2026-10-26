from django.contrib import admin

from .models import (
    Cart,
    CartItem,
    Category,
    Mahsulot,
    Order,
    OrderItem,
    ProductImage,
    Review,
    Wishlist,
)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 2


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("nomi",)
    search_fields = ("nomi",)


@admin.register(Mahsulot)
class MahsulotAdmin(admin.ModelAdmin):
    list_display = ("nomi", "narxi", "miqdori", "category", "korish", "slug")
    list_filter = ("category",)
    search_fields = ("nomi", "tavsifi")
    prepopulated_fields = {"slug": ("nomi",)}
    inlines = [ProductImageInline]
    readonly_fields = ("korish", "created", "updated")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("mahsulot", "user", "rating", "created")
    list_filter = ("rating", "created")
    search_fields = ("comment", "user__username", "mahsulot__nomi")
    readonly_fields = ("created",)


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "mahsulot", "created_at")
    search_fields = ("user__username", "mahsulot__nomi")
    readonly_fields = ("created_at",)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "created_at")
    inlines = [CartItemInline]
    readonly_fields = ("created_at",)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("mahsulot", "nomi", "narxi", "quantity")
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "ism", "telefon", "email", "status", "created")
    list_filter = ("status", "created")
    list_editable = ("status",)
    search_fields = ("ism", "telefon", "email", "user__username")
    readonly_fields = ("created",)
    inlines = [OrderItemInline]
