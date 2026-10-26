from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("wishlist/", views.wishlist_list, name="wishlist_list"),
    path("wishlist/toggle/<int:product_id>/", views.toggle_wishlist, name="toggle_wishlist"),
    path("products/<slug:slug>/", views.product_view, name="products-view"),
    path("login/", views.login_form, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("cart/", views.cart_detail, name="cart"),
    path("cart/add/<slug:slug>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:item_id>/<str:action>/", views.update_cart_item, name="cart_update"),
    path("cart/remove/<int:item_id>/", views.remove_cart_item, name="cart_remove"),
    path("checkout/", views.checkout, name="checkout"),
    path("checkout/verify/", views.checkout_verify, name="checkout_verify"),
    path("checkout/resend/", views.resend_code, name="resend_code"),
    path("orders/", views.orders_list, name="orders"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/cancel/", views.cancel_order, name="order_cancel"),
]
