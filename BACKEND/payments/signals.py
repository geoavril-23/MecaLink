from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
from breakdowns.models import Breakdown
from breakdowns.utils import haversine_distance
from .models import Payment

@receiver(post_save, sender=Breakdown)
def create_payment_for_breakdown(sender, instance, created, **kwargs):
    if created:
        distance_fee = Decimal('0.00')
        # Si le mécanicien ou le profil mécanicien a des coordonnées, on peut calculer les frais de distance (ex: 500 FCFA / km)
        if instance.mechanic and hasattr(instance.mechanic, 'mechanic_profile'):
            profile = instance.mechanic.mechanic_profile
            if profile.latitude and profile.longitude:
                dist = haversine_distance(profile.latitude, profile.longitude, instance.latitude, instance.longitude)
                if dist:
                    # 500 XOF par km de distance
                    distance_fee = (Decimal(str(dist)) * Decimal('500.00')).quantize(Decimal('0.01'))

        Payment.objects.create(
            breakdown=instance,
            user=instance.client,
            base_fee=Decimal('3000.00'),
            distance_fee=distance_fee
        )
