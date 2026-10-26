from django.db.models import Sum

from .models import CartItem


def cart_count(request):
    """Navbar uchun savatchadagi mahsulotlar soni (savatcha yaratmaydi)."""
    if request.user.is_authenticated:
        qs = CartItem.objects.filter(cart__user=request.user)
    else:
        cart_id = request.session.get("cart_id")
        if not cart_id:
            return {"cart_count": 0}
        qs = CartItem.objects.filter(cart_id=cart_id, cart__user=None)
    return {"cart_count": qs.aggregate(n=Sum("quantity"))["n"] or 0}
