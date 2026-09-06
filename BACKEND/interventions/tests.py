from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User, MechanicProfile
from vehicles.models import Vehicle
from breakdowns.models import Breakdown
from .models import Intervention

class InterventionAPITests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="interv_client",
            email="interv_client@example.com",
            password="Password123",
            telephone="+2250101010099",
            role="USAGER"
        )
        self.mechanic_user = User.objects.create_user(
            username="interv_mechanic",
            email="interv_mechanic@example.com",
            password="Password123",
            telephone="+2250707070099",
            role="MECANICIEN"
        )
        MechanicProfile.objects.create(
            user=self.mechanic_user,
            specialite="Diagnostic & Moteur",
            garage_name="Garage Express",
            latitude=5.3500,
            longitude=-4.0300,
            est_disponible=True
        )
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            make="Toyota",
            model="Camry",
            license_plate="2222-YY-02"
        )
        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)

        self.mechanic_api = APIClient()
        self.mechanic_api.force_authenticate(user=self.mechanic_user)

        self.breakdown = Breakdown.objects.create(
            client=self.client_user,
            vehicle=self.vehicle,
            latitude=5.3400,
            longitude=-4.0200,
            description="Radiateur en surchauffe"
        )

    def test_start_intervention_updates_breakdown_status(self):
        start_url = reverse('intervention-start-intervention')
        
        # 1. Regular usager cannot start intervention
        unauth_res = self.client_api.post(start_url, {"breakdown": self.breakdown.id}, format='json')
        self.assertEqual(unauth_res.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Mechanic starts intervention
        res = self.mechanic_api.post(start_url, {"breakdown": self.breakdown.id}, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        self.breakdown.refresh_from_db()
        self.assertEqual(self.breakdown.status, 'IN_PROGRESS')
        self.assertEqual(self.breakdown.mechanic, self.mechanic_user)

        intervention = Intervention.objects.get(breakdown=self.breakdown)
        self.assertEqual(intervention.status, 'IN_PROGRESS')
        self.assertEqual(intervention.mechanic, self.mechanic_user)

    def test_complete_intervention_updates_breakdown_to_completed(self):
        # 1. Start intervention
        intervention = Intervention.objects.create(
            breakdown=self.breakdown,
            mechanic=self.mechanic_user,
            status='IN_PROGRESS'
        )
        self.breakdown.status = 'IN_PROGRESS'
        self.breakdown.mechanic = self.mechanic_user
        self.breakdown.save()

        complete_url = reverse('intervention-complete-intervention', kwargs={'pk': intervention.id})
        data = {
            "diagnostic_notes": "Remplacement de la pompe à eau et du liquide de refroidissement.",
            "parts_replaced": ["Pompe à eau", "Durite de refroidissement"]
        }
        res = self.mechanic_api.post(complete_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        intervention.refresh_from_db()
        self.assertEqual(intervention.status, 'COMPLETED')
        self.assertIsNotNone(intervention.end_time)
        self.assertEqual(intervention.diagnostic_notes, "Remplacement de la pompe à eau et du liquide de refroidissement.")
        self.assertEqual(len(intervention.parts_replaced), 2)

        self.breakdown.refresh_from_db()
        self.assertEqual(self.breakdown.status, 'COMPLETED')
