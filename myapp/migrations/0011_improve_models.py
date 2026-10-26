# Generated manually for quality improvements

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("myapp", "0010_alter_mahsulot_image"),
    ]

    operations = [
        # Catgeory → Category (Python name), jadval nomi o'zgarmaydi
        migrations.RenameModel(
            old_name="Catgeory",
            new_name="Category",
        ),
        migrations.AlterModelOptions(
            name="category",
            options={
                "ordering": ["nomi"],
                "verbose_name": "Kategoriya",
                "verbose_name_plural": "Kategoriyalar",
            },
        ),
        migrations.AlterModelTable(
            name="category",
            table="myapp_catgeory",
        ),
        # Mahsulot yaxshilanishlari
        migrations.AlterModelOptions(
            name="mahsulot",
            options={
                "ordering": ["-id"],
                "verbose_name": "Mahsulot",
                "verbose_name_plural": "Mahsulotlar",
            },
        ),
        migrations.AddField(
            model_name="mahsulot",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, null=True, verbose_name="Yaratilgan"
            ),
        ),
        migrations.AddField(
            model_name="mahsulot",
            name="updated",
            field=models.DateTimeField(
                auto_now=True, null=True, verbose_name="Yangilangan"
            ),
        ),
        migrations.AlterField(
            model_name="mahsulot",
            name="category",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="mahsulotlar",
                to="myapp.category",
                verbose_name="Kategoriya",
            ),
        ),
        migrations.AlterField(
            model_name="mahsulot",
            name="miqdori",
            field=models.PositiveIntegerField(
                default=0, verbose_name="Ombordagi miqdor"
            ),
        ),
        migrations.AlterField(
            model_name="mahsulot",
            name="narxi",
            field=models.PositiveIntegerField(verbose_name="Narx"),
        ),
        migrations.AlterField(
            model_name="mahsulot",
            name="tavsifi",
            field=models.TextField(blank=True, verbose_name="Tavsif"),
        ),
        migrations.AlterField(
            model_name="mahsulot",
            name="image",
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to="mahsulotlar/",
                verbose_name="Asosiy rasm",
            ),
        ),
        # Review unique_together + Meta
        migrations.AlterModelOptions(
            name="review",
            options={
                "ordering": ["-created"],
                "verbose_name": "Sharh",
                "verbose_name_plural": "Sharhlar",
            },
        ),
        migrations.AlterUniqueTogether(
            name="review",
            unique_together={("mahsulot", "user")},
        ),
        migrations.AlterField(
            model_name="review",
            name="rating",
            field=models.PositiveSmallIntegerField(
                choices=[
                    (1, "1 yulduz"),
                    (2, "2 yulduz"),
                    (3, "3 yulduz"),
                    (4, "4 yulduz"),
                    (5, "5 yulduz"),
                ],
                default=5,
                verbose_name="Reyting",
            ),
        ),
        # Ishlatilmagan Member modelini olib tashlash
        migrations.DeleteModel(
            name="Member",
        ),
    ]
