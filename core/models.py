import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile
from io import BytesIO


class Category(models.Model):
    name  = models.CharField(max_length=100, verbose_name=_('Nom'))
    slug  = models.SlugField(unique=True)
    icon  = models.CharField(max_length=10, default='📦', verbose_name=_('Icône'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Ordre'))

    class Meta:
        verbose_name        = _('Catégorie')
        verbose_name_plural = _('Catégories')
        ordering            = ['order']

    def __str__(self):
        return f"{self.icon} {self.name}"


class Product(models.Model):
    category    = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products', verbose_name=_('Catégorie'))
    name        = models.CharField(max_length=200, verbose_name=_('Nom'))
    description = models.TextField(blank=True, verbose_name=_('Description'))
    price       = models.DecimalField(max_digits=6, decimal_places=2, verbose_name=_('Prix (€)'))
    image       = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name=_('Photo'))
    emoji       = models.CharField(max_length=10, default='📦', verbose_name=_('Emoji (fallback)'))
    in_stock    = models.BooleanField(default=True, verbose_name=_('En stock'))
    featured    = models.BooleanField(default=False, verbose_name=_('Meilleure vente'))
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = _('Produit')
        verbose_name_plural = _('Produits')
        ordering            = ['category__order', 'name']

    def __str__(self):
        return f"{self.emoji} {self.name} — {self.price}€"

    def save(self, *args, **kwargs):
        if self.image:
            self._optimize_image()
        super().save(*args, **kwargs)

    def _optimize_image(self):
        from PIL import Image
        try:
            img = Image.open(self.image)
        except Exception:
            return

        # Convertir en RGB si nécessaire (PNG RGBA, etc.)
        if img.mode in ('RGBA', 'P', 'LA'):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = bg
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Redimensionner si plus grand que 800×800
        max_size = (800, 800)
        if img.width > max_size[0] or img.height > max_size[1]:
            img.thumbnail(max_size, Image.LANCZOS)

        # Sauvegarder en WebP (meilleure compression)
        buf = BytesIO()
        img.save(buf, format='WEBP', quality=82, method=6)
        buf.seek(0)

        # Remplacer le fichier par le WebP optimisé
        old_name = os.path.splitext(os.path.basename(self.image.name))[0]
        new_name = f"{old_name}.webp"
        self.image.save(new_name, ContentFile(buf.read()), save=False)


class Order(models.Model):
    STATUS_CHOICES = [
        ('en_attente',    _('En attente')),
        ('confirmee',     _('Confirmée')),
        ('en_livraison',  _('En livraison')),
        ('devant_maison', _('Devant chez vous')),
        ('livree',        _('Livrée')),
        ('annulee',       _('Annulée')),
    ]
    PAYMENT_CHOICES = [
        ('livraison', _('Paiement à la livraison')),
    ]

    client_name      = models.CharField(max_length=150, verbose_name=_('Prénom'))
    phone            = models.CharField(max_length=20, verbose_name=_('Téléphone'))
    address          = models.CharField(max_length=255, verbose_name=_('Adresse de livraison'))
    payment_method   = models.CharField(max_length=20, choices=PAYMENT_CHOICES, verbose_name=_('Paiement'))
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default='en_attente', verbose_name=_('Statut'))
    tracking_number  = models.CharField(max_length=8, unique=True, blank=True, verbose_name=_('N° de suivi'))
    notes            = models.TextField(blank=True, verbose_name=_('Notes'))
    created_at       = models.DateTimeField(auto_now_add=True, verbose_name=_('Passée le'))

    class Meta:
        verbose_name        = _('Commande')
        verbose_name_plural = _('Commandes')
        ordering            = ['-created_at']

    def __str__(self):
        return f"Commande #{self.pk} — {self.client_name}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())


class SupportSession(models.Model):
    """Conversation de support entre un visiteur et l'admin."""
    session_key  = models.CharField(max_length=64, unique=True, db_index=True)
    visitor_name = models.CharField(max_length=100, default='Visiteur')
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.visitor_name} — {self.created_at.strftime('%d/%m %H:%M')}"

    def unread_count(self):
        return self.support_messages.filter(is_admin=False, is_read=False).count()


class SupportMessage(models.Model):
    session    = models.ForeignKey(SupportSession, on_delete=models.CASCADE, related_name='support_messages')
    content    = models.TextField()
    is_admin   = models.BooleanField(default=False)
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']


class OrderMessage(models.Model):
    order      = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='messages')
    content    = models.TextField(verbose_name=_('Message'))
    is_admin   = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        who = 'Admin' if self.is_admin else self.order.client_name
        return f"[{who}] {self.content[:60]}"


class OrderItem(models.Model):
    order        = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product      = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, verbose_name=_('Produit'))
    product_name = models.CharField(max_length=200)   # snapshot
    unit_price   = models.DecimalField(max_digits=6, decimal_places=2)  # snapshot
    quantity     = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity}× {self.product_name}"

    @property
    def subtotal(self):
        return self.unit_price * self.quantity
