from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("myapp", "0009_review"),
    ]

    operations = [
        migrations.AlterField(
            model_name="mahsulot",
            name="image",
            field=models.ImageField(upload_to="mahsulotlar/"),
        ),
    ]
