from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('USAGER', 'Usager'),
        ('MECANICIEN', 'Mécanicien'),
        ('ADMINISTRATEUR', 'Administrateur'),
    )
    telephone = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='USAGER')


class MechanicProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='mechanic_profile'
    )
    specialite = models.CharField(max_length=100)
    garage_name = models.CharField(max_length=150, blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    est_disponible = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profil Mécanicien - {self.user.username}"