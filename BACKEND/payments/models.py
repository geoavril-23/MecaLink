from django.db import models
from django.conf import settings
from decimal import Decimal
from breakdowns.models import Breakdown

class Payment(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('HELD_IN_ESCROW', 'Sous séquestre'),
        ('RELEASED', 'Libéré'),
        ('REFUNDED', 'Remboursé'),
        ('FAILED', 'Échoué'),
    ]

    breakdown = models.OneToOneField(
        Breakdown,
        on_delete=models.CASCADE,
        related_name='payment'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments_made'
    )
    base_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('3000.00'))
    distance_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2)  # 10%
    mechanic_payout = models.DecimalField(max_digits=10, decimal_places=2)      # 90%
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    NETWORK_CHOICES = [
        ('TMONEY', 'TMONEY'),
        ('FLOOZ', 'FLOOZ'),
    ]

    phone_number = models.CharField(max_length=20, null=True, blank=True)
    network = models.CharField(max_length=10, choices=NETWORK_CHOICES, null=True, blank=True)
    paygate_tx_reference = models.CharField(max_length=100, null=True, blank=True)
    transaction_reference = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.base_fee is not None and self.distance_fee is not None:
            self.total_amount = Decimal(str(self.base_fee)) + Decimal(str(self.distance_fee))
            self.platform_commission = (self.total_amount * Decimal('0.10')).quantize(Decimal('0.01'))
            self.mechanic_payout = (self.total_amount * Decimal('0.90')).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Paiement #{self.id} - Panne #{self.breakdown_id} ({self.status})"
