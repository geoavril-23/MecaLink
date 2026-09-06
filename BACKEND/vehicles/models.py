from django.db import models
from django.conf import settings

class Vehicle(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='vehicles'
    )
    make = models.CharField(max_length=50)        # Ex: Toyota
    model = models.CharField(max_length=50)       # Ex: Corolla
    year = models.PositiveIntegerField(null=True, blank=True)
    license_plate = models.CharField(max_length=20, unique=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.make} {self.model} ({self.license_plate})"