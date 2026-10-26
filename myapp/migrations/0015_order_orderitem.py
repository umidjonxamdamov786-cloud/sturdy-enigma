import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0014_cart_cartitem'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ism', models.CharField(max_length=150, verbose_name='Ism')),
                ('telefon', models.CharField(max_length=20, verbose_name='Telefon')),
                ('manzil', models.TextField(verbose_name='Manzil')),
                ('izoh', models.TextField(blank=True, verbose_name='Izoh')),
                ('status', models.CharField(choices=[('new', 'Yangi'), ('processing', 'Jarayonda'), ('delivered', 'Yetkazildi'), ('cancelled', 'Bekor qilindi')], default='new', max_length=20, verbose_name='Holati')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Sana')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Foydalanuvchi')),
            ],
            options={
                'verbose_name': 'Buyurtma',
                'verbose_name_plural': 'Buyurtmalar',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nomi', models.CharField(max_length=200, verbose_name='Nomi')),
                ('narxi', models.PositiveIntegerField(verbose_name='Narx')),
                ('quantity', models.PositiveIntegerField(default=1, verbose_name='Miqdor')),
                ('mahsulot', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='myapp.mahsulot', verbose_name='Mahsulot')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='myapp.order', verbose_name='Buyurtma')),
            ],
            options={
                'verbose_name': 'Buyurtma mahsuloti',
                'verbose_name_plural': 'Buyurtma mahsulotlari',
            },
        ),
    ]
