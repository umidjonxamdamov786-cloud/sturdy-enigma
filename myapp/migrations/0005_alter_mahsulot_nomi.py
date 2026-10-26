from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0004_delete_product"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mahsulot",
            name="nomi",
            field=models.CharField(max_length=200, verbose_name="Mahsulot nomi"),
        ),
    ]
