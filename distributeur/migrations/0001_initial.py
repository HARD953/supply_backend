# Generated by Django 5.1.4 on 2024-12-17 13:13

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom')),
                ('icon', models.CharField(blank=True, max_length=50, null=True, verbose_name='Icône')),
                ('color', models.CharField(default='#607D8B', max_length=7, verbose_name='Couleur')),
                ('background_color', models.CharField(default='#ECEFF1', max_length=7, verbose_name='Couleur de fond')),
            ],
            options={
                'verbose_name': 'Catégorie',
                'verbose_name_plural': 'Catégories',
            },
        ),
        migrations.CreateModel(
            name='ProductFormat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nom du format')),
                ('volume', models.CharField(max_length=50, verbose_name='Volume')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix')),
                ('stock', models.PositiveIntegerField(verbose_name='Stock')),
            ],
            options={
                'verbose_name': 'Format de produit',
                'verbose_name_plural': 'Formats de produit',
            },
        ),
        migrations.CreateModel(
            name='Supplier',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, unique=True, verbose_name='Nom')),
                ('contact_email', models.EmailField(blank=True, max_length=254, null=True, verbose_name='Email de contact')),
                ('phone_number', models.CharField(blank=True, max_length=20, null=True, verbose_name='Numéro de téléphone')),
            ],
            options={
                'verbose_name': 'Fournisseur',
                'verbose_name_plural': 'Fournisseurs',
            },
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créée le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Mise à jour le')),
                ('status', models.CharField(choices=[('pending', 'En attente'), ('processing', 'En cours'), ('completed', 'Terminée'), ('cancelled', 'Annulée')], default='pending', max_length=20, verbose_name='Statut')),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Montant total')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL, verbose_name='Utilisateur')),
            ],
            options={
                'verbose_name': 'Commande',
                'verbose_name_plural': 'Commandes',
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='Nom')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix')),
                ('stock', models.PositiveIntegerField(verbose_name='Stock total')),
                ('min_stock', models.PositiveIntegerField(default=50, verbose_name='Stock minimum')),
                ('image', models.ImageField(blank=True, null=True, upload_to='product_images/', verbose_name='Image')),
                ('last_order_date', models.DateField(blank=True, null=True, verbose_name='Date dernière commande')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='distributeur.category', verbose_name='Catégorie')),
                ('formats', models.ManyToManyField(related_name='products', to='distributeur.productformat', verbose_name='Formats disponibles')),
                ('supplier', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='products', to='distributeur.supplier', verbose_name='Fournisseur')),
            ],
            options={
                'verbose_name': 'Produit',
                'verbose_name_plural': 'Produits',
            },
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(verbose_name='Quantité')),
                ('unit_price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Prix unitaire')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='distributeur.order', verbose_name='Commande')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='distributeur.product', verbose_name='Produit')),
                ('product_format', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='distributeur.productformat', verbose_name='Format du produit')),
            ],
            options={
                'verbose_name': 'Article de commande',
                'verbose_name_plural': 'Articles de commande',
            },
        ),
    ]