from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def likes_to_wishlist(apps, schema_editor):
    """Eski 'like' (Yoqtirish) ma'lumotlarini Wishlist ga ko'chiradi."""
    Mahsulot = apps.get_model("myapp", "Mahsulot")
    Wishlist = apps.get_model("myapp", "Wishlist")
    Through = Mahsulot._meta.get_field("like").remote_field.through

    Wishlist.objects.bulk_create(
        [
            Wishlist(user_id=row.user_id, mahsulot_id=row.mahsulot_id)
            for row in Through.objects.all()
        ],
        ignore_conflicts=True,
    )


def wishlist_to_likes(apps, schema_editor):
    Mahsulot = apps.get_model("myapp", "Mahsulot")
    Wishlist = apps.get_model("myapp", "Wishlist")
    Through = Mahsulot._meta.get_field("like").remote_field.through

    Through.objects.bulk_create(
        [
            Through(mahsulot_id=w.mahsulot_id, user_id=w.user_id)
            for w in Wishlist.objects.all()
        ],
        ignore_conflicts=True,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0012_sync_model_state"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Wishlist",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan")),
                (
                    "mahsulot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlisted_by",
                        to="myapp.mahsulot",
                        verbose_name="Mahsulot",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wishlist",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Foydalanuvchi",
                    ),
                ),
            ],
            options={
                "verbose_name": "Sevimli mahsulot",
                "verbose_name_plural": "Sevimli mahsulotlar",
                "ordering": ["-created_at"],
                "unique_together": {("user", "mahsulot")},
            },
        ),
        migrations.RunPython(likes_to_wishlist, wishlist_to_likes),
        migrations.RemoveField(model_name="mahsulot", name="like"),
    ]
