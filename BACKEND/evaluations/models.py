from django.db import models
from django.conf import settings
from breakdowns.models import Breakdown

class Evaluation(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    breakdown = models.OneToOneField(
        Breakdown,
        on_delete=models.CASCADE,
        related_name='evaluation'
    )
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='given_evaluations'
    )
    mechanic = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_evaluations'
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Évaluation #{self.id} - Note {self.rating}/5 pour {self.mechanic.username}"
