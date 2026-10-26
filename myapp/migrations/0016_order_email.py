from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0015_order_orderitem'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Email'),
        ),
    ]
