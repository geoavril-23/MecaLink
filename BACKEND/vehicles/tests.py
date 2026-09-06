from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User
from .models import Vehicle

class VehicleAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="vehuser",
            password="Password123",
            telephone="+2250101010101",
            role="USAGER"
        )
        self.client.force_authenticate(user=self.user)
        self.vehicles_url = reverse('vehicle-list')

    def test_create_vehicle(self):
        data = {
            "make": "Toyota",
            "model": "Corolla",
            "year": 2020,
            "license_plate": "1234-AB-01",
            "color": "Gris"
        }
        response = self.client.post(self.vehicles_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vehicle.objects.count(), 1)
        self.assertEqual(Vehicle.objects.first().owner, self.user)

    def test_get_vehicles_filtered_by_owner(self):
        Vehicle.objects.create(
            owner=self.user,
            make="Honda",
            model="Civic",
            license_plate="5678-CD-02"
        )
        other_user = User.objects.create_user(
            username="other",
            password="Password123",
            telephone="+2250202020202"
        )
        Vehicle.objects.create(
            owner=other_user,
            make="Peugeot",
            model="208",
            license_plate="9999-ZZ-99"
        )
        response = self.client.get(self.vehicles_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['license_plate'], "5678-CD-02")
