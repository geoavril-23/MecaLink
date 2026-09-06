from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User, MechanicProfile
from vehicles.models import Vehicle
from breakdowns.models import Breakdown
from payments.models import Payment
from .models import Evaluation

class EvaluationAPITests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="eval_client",
            email="eval_client@example.com",
            password="Password123",
            telephone="+2250101010088",
            role="USAGER"
        )
        self.mechanic_user = User.objects.create_user(
            username="eval_mechanic",
            email="eval_mechanic@example.com",
            password="Password123",
            telephone="+2250707070088",
            role="MECANICIEN"
        )
        MechanicProfile.objects.create(
            user=self.mechanic_user,
            specialite="Freinage & Suspension",
            garage_name="Garage AutoTop",
            latitude=5.3500,
            longitude=-4.0300,
            est_disponible=True
        )
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            make="Renault",
            model="Duster",
            license_plate="3333-ZZ-03"
        )
        self.client_api = APIClient()
        self.client_api.force_authenticate(user=self.client_user)

        self.mechanic_api = APIClient()
        self.mechanic_api.force_authenticate(user=self.mechanic_user)

        self.breakdown = Breakdown.objects.create(
            client=self.client_user,
            mechanic=self.mechanic_user,
            vehicle=self.vehicle,
            latitude=5.3400,
            longitude=-4.0200,
            description="Plaquettes de frein usées"
        )

    def test_evaluation_requires_completed_breakdown_and_released_payment(self):
        eval_url = reverse('evaluation-list')
        data = {
            "breakdown": self.breakdown.id,
            "rating": 5,
            "comment": "Travail très propre et rapide !"
        }

        # 1. Attempt evaluation while breakdown is PENDING -> fail
        res = self.client_api.post(eval_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Update breakdown status to COMPLETED but payment is still PENDING -> fail
        self.breakdown.status = 'COMPLETED'
        self.breakdown.save()

        res = self.client_api.post(eval_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Update payment status to RELEASED -> succeed
        payment = self.breakdown.payment
        payment.status = 'RELEASED'
        payment.save()

        res = self.client_api.post(eval_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Evaluation.objects.count(), 1)
        
        evaluation = Evaluation.objects.first()
        self.assertEqual(evaluation.rating, 5)
        self.assertEqual(evaluation.mechanic, self.mechanic_user)

    def test_mechanic_evaluations_average_rating_endpoint(self):
        # Create 2 completed & evaluated breakdowns for mechanic
        b1 = Breakdown.objects.create(client=self.client_user, mechanic=self.mechanic_user, vehicle=self.vehicle, latitude=5.3, longitude=-4.0, description="P1", status='COMPLETED')
        b1.payment.status = 'RELEASED'
        b1.payment.save()
        Evaluation.objects.create(breakdown=b1, client=self.client_user, mechanic=self.mechanic_user, rating=4, comment="Bon travail")

        b2 = Breakdown.objects.create(client=self.client_user, mechanic=self.mechanic_user, vehicle=self.vehicle, latitude=5.3, longitude=-4.0, description="P2", status='COMPLETED')
        b2.payment.status = 'RELEASED'
        b2.payment.save()
        Evaluation.objects.create(breakdown=b2, client=self.client_user, mechanic=self.mechanic_user, rating=5, comment="Parfait !")

        url = reverse('evaluation-mechanic-evaluations', kwargs={'mechanic_id': self.mechanic_user.id})
        res = self.client_api.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['total_evaluations'], 2)
        self.assertEqual(res.data['average_rating'], 4.5)
