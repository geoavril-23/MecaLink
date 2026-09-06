from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from .models import User, MechanicProfile

class UserAuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')

    def test_register_usager_success(self):
        data = {
            "username": "client1",
            "email": "client1@example.com",
            "telephone": "+2250102030405",
            "role": "USAGER",
            "password": "SecurePassword123"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="client1").exists())

    def test_register_mechanic_success(self):
        data = {
            "username": "meca1",
            "email": "meca1@example.com",
            "telephone": "+2250708091011",
            "role": "MECANICIEN",
            "password": "SecurePassword123",
            "mechanic_profile": {
                "specialite": "Moteur & Freinage",
                "garage_name": "Garage AutoPro",
                "latitude": 5.3485,
                "longitude": -4.0305,
                "est_disponible": True
            }
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="meca1")
        self.assertEqual(user.role, "MECANICIEN")
        self.assertTrue(MechanicProfile.objects.filter(user=user).exists())

    def test_login_success(self):
        User.objects.create_user(
            username="testuser",
            password="Password123",
            telephone="+2250000000000",
            role="USAGER"
        )
        response = self.client.post(self.login_url, {
            "username": "testuser",
            "password": "Password123"
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
