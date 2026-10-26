from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    """Model va migratsiya holatini moslashtirish (verbose_name, related_name)."""

    dependencies = [
        ("myapp", "0011_improve_models"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="category",
            name="nomi",
            field=models.CharField(max_length=200, verbose_name="Nomi"),
        ),
        migrations.AlterField(
            model_name="mahsulot",
            name="slug",
            field=models.SlugField(blank=True, null=True, unique=True, verbose_name="Slug"),
        ),
        migrations.AlterField(
            model_name="mahsulot",
            name="korish",
            field=models.PositiveIntegerField(default=0, verbose_name="Ko'rishlar soni"),
        ),
        migrations.AlterField(
            model_name="mahsulot",
            name="like",
            field=models.ManyToManyField(
                blank=True,
                related_name="like",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Yoqtirganlar",
            ),
        ),
        migrations.AlterModelOptions(
            name="productimage",
            options={
                "verbose_name": "Qo'shimcha rasm",
                "verbose_name_plural": "Qo'shimcha rasmlar",
            },
        ),
        migrations.AlterField(
            model_name="productimage",
            name="image",
            field=models.ImageField(upload_to="products/", verbose_name="Rasm"),
        ),
        migrations.AlterField(
            model_name="review",
            name="mahsulot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews",
                to="myapp.mahsulot",
                verbose_name="Mahsulot",
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reviews",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Foydalanuvchi",
            ),
        ),
        migrations.AlterField(
            model_name="review",
            name="comment",
            field=models.TextField(verbose_name="Izoh"),
        ),
    ]
