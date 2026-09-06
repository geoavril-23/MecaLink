from django.db import models
from django.conf import settings
from breakdowns.models import Breakdown

class Intervention(models.Model):
    STATUS_CHOICES = [
        ('IN_PROGRESS', 'En cours'),
        ('COMPLETED', 'Terminée'),
        ('CANCELLED', 'Annulée'),
    ]

    breakdown = models.OneToOneField(
        Breakdown,
        on_delete=models.CASCADE,
        related_name='intervention'
    )
    mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'MECANICIEN'},
        related_name='interventions'
    )
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    diagnostic_notes = models.TextField(blank=True, null=True)
    parts_replaced = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Intervention #{self.id} - Panne #{self.breakdown_id} ({self.status})"
