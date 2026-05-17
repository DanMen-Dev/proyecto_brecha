#Copyright (c) 2026 Daniel Mendoza (HierroEnLinea). Licensed under the MIT License.
from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Product(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True) # El dueño
    sku = models.CharField(max_length=100) # Quitamos el unique=True para que dos usuarios puedan tener el mismo SKU
    name = models.CharField(max_length=255)
    cost_usd_normal = models.DecimalField(max_digits=10, decimal_places=2)
    cost_usd_offer = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_cashea_base = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    price_cashea_base_offer = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username if self.user else 'System'} - {self.sku}"     

class DailyRate(models.Model):
    date = models.DateField(unique=True)
    bcv_rate = models.DecimalField(max_digits=12, decimal_places=4)
    binance_rate = models.DecimalField(max_digits=12, decimal_places=4)
    gap_percentage = models.DecimalField(max_digits=10, decimal_places=4)

    def __str__(self):
        return f"{self.date} - BCV: {self.bcv_rate}"


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_pro = models.BooleanField(default=False) # Switch de monetización
    subscription_expires = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {'PRO' if self.is_pro else 'FREE'}"

# RECEPTOR AUTOMÁTICO: Crea el perfil apenas se registre un usuario
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class SubscriptionRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    referencia_pago = models.CharField(max_length=50, verbose_name="Referencia Pago Móvil / P2P")
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    procesado = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __str__(self):
        return f"Solicitud de {self.user.username} - Ref: {self.referencia_pago}"        