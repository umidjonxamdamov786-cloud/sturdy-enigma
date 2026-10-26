from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0006_mahsulot_slug_alter_mahsulot_miqdori"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="products/", verbose_name="Qo‘shimcha rasm")),
                ("product", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="myapp.mahsulot", verbose_name="Mahsulot")),
            ],
        ),
    ]
