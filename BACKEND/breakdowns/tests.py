from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User, MechanicProfile
from vehicles.models import Vehicle
from .models import Breakdown
from .utils import haversine_distance

class BreakdownAPITests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="client_test",
            password="Password123",
            telephone="+2250100000001",
            role="USAGER"
        )
        self.mechanic_user = User.objects.create_user(
            username="mechanic_test",
            password="Password123",
            telephone="+2250700000002",
            role="MECANICIEN"
        )
        MechanicProfile.objects.create(
            user=self.mechanic_user,
            specialite="Electronique",
            garage_name="Garage Express",
            latitude=5.3485,
            longitude=-4.0305,
            est_disponible=True
        )
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            make="Nissan",
            model="Qashqai",
            license_plate="AB-123-CD"
        )
        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)

        self.mechanic_api = APIClient()
        self.mechanic_api.force_authenticate(user=self.mechanic_user)

    def test_haversine_distance_function(self):
        # Abidjan Plateau (5.32, -4.02) to Marcory (5.30, -3.98) ~ 4.9 km
        dist = haversine_distance(5.32, -4.02, 5.30, -3.98)
        self.assertIsNotNone(dist)
        self.assertAlmostEqual(dist, 4.9, delta=1.0)

    def test_create_breakdown(self):
        url = reverse('breakdown-list')
        data = {
            "vehicle": self.vehicle.id,
            "latitude": 5.3400,
            "longitude": -4.0300,
            "description": "Batterie à plat au carrefour"
        }
        response = self.client_api.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Breakdown.objects.count(), 1)
        breakdown = Breakdown.objects.first()
        self.assertEqual(breakdown.client, self.client_user)
        self.assertEqual(breakdown.status, 'PENDING')

    def test_pending_breakdowns_haversine_filtering(self):
        # Create 2 breakdowns: one close (2km), one far (50km)
        b_close = Breakdown.objects.create(
            client=self.client_user,
            vehicle=self.vehicle,
            latitude=5.3500,
            longitude=-4.0300,
            description="Panne proche"
        )
        b_far = Breakdown.objects.create(
            client=self.client_user,
            vehicle=self.vehicle,
            latitude=5.8000,
            longitude=-4.5000,
            description="Panne distante"
        )

        url = reverse('breakdown-pending') + "?lat=5.3485&lon=-4.0305&radius=10"
        response = self.mechanic_api.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], b_close.id)
        self.assertIsNotNone(response.data[0]['distance_km'])

    def test_breakdown_full_lifecycle(self):
        breakdown = Breakdown.objects.create(
            client=self.client_user,
            vehicle=self.vehicle,
            latitude=5.3400,
            longitude=-4.0300,
            description="Moteur surchauffe"
        )

        # 1. Accept breakdown as Mechanic
        accept_url = reverse('breakdown-accept', kwargs={'pk': breakdown.id})
        response = self.mechanic_api.patch(accept_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        breakdown.refresh_from_db()
        self.assertEqual(breakdown.status, 'ACCEPTED')
        self.assertEqual(breakdown.mechanic, self.mechanic_user)

        # Non-mechanic cannot accept
        unauth_response = self.client_api.patch(accept_url)
        self.assertEqual(unauth_response.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Transition to IN_PROGRESS
        in_progress_url = reverse('breakdown-in-progress', kwargs={'pk': breakdown.id})
        response = self.mechanic_api.patch(in_progress_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        breakdown.refresh_from_db()
        self.assertEqual(breakdown.status, 'IN_PROGRESS')

        # 3. Transition to COMPLETED
        complete_url = reverse('breakdown-complete', kwargs={'pk': breakdown.id})
        response = self.mechanic_api.patch(complete_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        breakdown.refresh_from_db()
        self.assertEqual(breakdown.status, 'COMPLETED')
