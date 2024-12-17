from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

class Category(models.Model):
    """Modèle pour les catégories de produits"""
    name = models.CharField(_('Nom'), max_length=100)
    icon = models.CharField(_('Icône'), max_length=50, blank=True, null=True)
    color = models.CharField(_('Couleur'), max_length=7, default='#607D8B')
    background_color = models.CharField(_('Couleur de fond'), max_length=7, default='#ECEFF1')

    class Meta:
        verbose_name = _('Catégorie')
        verbose_name_plural = _('Catégories')

    def __str__(self):
        return self.name

class Supplier(models.Model):
    """Modèle pour les fournisseurs"""
    name = models.CharField(_('Nom'), max_length=200, unique=True)
    contact_email = models.EmailField(_('Email de contact'), blank=True, null=True)
    phone_number = models.CharField(_('Numéro de téléphone'), max_length=20, blank=True, null=True)

    class Meta:
        verbose_name = _('Fournisseur')
        verbose_name_plural = _('Fournisseurs')

    def __str__(self):
        return self.name

class ProductFormat(models.Model):
    """Modèle pour les différents formats de produits"""
    name = models.CharField(_('Nom du format'), max_length=100)
    volume = models.CharField(_('Volume'), max_length=50)  # ex: '25cl', '50cl', '1L'
    price = models.DecimalField(_('Prix'), max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(_('Stock'))

    class Meta:
        verbose_name = _('Format de produit')
        verbose_name_plural = _('Formats de produit')

    def __str__(self):
        return f"{self.name} ({self.volume})"

class Product(models.Model):
    """Modèle principal pour les produits"""
    name = models.CharField(_('Nom'), max_length=200)
    supplier = models.ForeignKey(
        Supplier, 
        on_delete=models.SET_NULL, 
        related_name='products', 
        verbose_name=_('Fournisseur'),
        null=True
    )
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        related_name='products', 
        verbose_name=_('Catégorie'),
        null=True
    )
    price = models.DecimalField(_('Prix'), max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(_('Stock total'))
    min_stock = models.PositiveIntegerField(_('Stock minimum'), default=50)
    
    image = models.ImageField(
        _('Image'), 
        upload_to='product_images/', 
        blank=True, 
        null=True
    )
    
    formats = models.ManyToManyField(
        ProductFormat, 
        related_name='products', 
        verbose_name=_('Formats disponibles')
    )
    
    last_order_date = models.DateField(
        _('Date dernière commande'), 
        blank=True, 
        null=True
    )

    class Meta:
        verbose_name = _('Produit')
        verbose_name_plural = _('Produits')

    def __str__(self):
        return self.name
    
    def check_stock_availability(self, quantity):
        """
        Vérifie si la quantité demandée est disponible en stock
        
        Args:
            quantity (int): Quantité à vérifier
        
        Returns:
            bool: True si le stock est suffisant, False sinon
        """
        return self.stock >= quantity

    def reduce_stock(self, quantity):
        """
        Réduit le stock du produit
        
        Args:
            quantity (int): Quantité à réduire du stock
        
        Raises:
            ValidationError: Si la quantité demandée excède le stock disponible
        """
        if not self.check_stock_availability(quantity):
            raise ValidationError(
                _('Stock insuffisant. Stock disponible : %(stock)d, Quantité demandée : %(quantity)d'),
                params={
                    'stock': self.stock,
                    'quantity': quantity
                }
            )
        
        self.stock -= quantity
        self.save()

    def restore_stock(self, quantity):
        """
        Restaure la quantité au stock (utile pour l'annulation de commande)
        
        Args:
            quantity (int): Quantité à ajouter au stock
        """
        self.stock += quantity
        self.save()

class Order(models.Model):
    """Modèle pour les commandes"""
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processing', _('En cours')),
        ('completed', _('Terminée')),
        ('cancelled', _('Annulée'))
    ]

    user = models.ForeignKey(
        'auth.User', 
        on_delete=models.CASCADE, 
        related_name='orders',
        verbose_name=_('Utilisateur')
    )
    
    created_at = models.DateTimeField(_('Créée le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Mise à jour le'), auto_now=True)
    
    status = models.CharField(
        _('Statut'), 
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )

    total_amount = models.DecimalField(
        _('Montant total'), 
        max_digits=10, 
        decimal_places=2
    )

    class Meta:
        verbose_name = _('Commande')
        verbose_name_plural = _('Commandes')

    def __str__(self):
        return f"Commande {self.id} - {self.user.username}"

class OrderItem(models.Model):
    """Modèle pour les éléments de commande"""
    order = models.ForeignKey(
        Order, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name=_('Commande')
    )
    
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE,
        verbose_name=_('Produit')
    )
    
    product_format = models.ForeignKey(
        ProductFormat, 
        on_delete=models.CASCADE,
        verbose_name=_('Format du produit')
    )
    
    quantity = models.PositiveIntegerField(_('Quantité'))
    
    unit_price = models.DecimalField(
        _('Prix unitaire'), 
        max_digits=10, 
        decimal_places=2
    )

    class Meta:
        verbose_name = _('Article de commande')
        verbose_name_plural = _('Articles de commande')

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour vérifier le stock avant la création
        """
        # Vérifier le stock avant de créer l'item de commande
        if not self.product.check_stock_availability(self.quantity):
            raise ValidationError(
                _('Stock insuffisant pour le produit %(product)s'),
                params={'product': self.product.name}
            )
        
        # Réduire le stock lors de la création de l'item de commande
        self.product.reduce_stock(self.quantity)
        
        super().save(*args, **kwargs)