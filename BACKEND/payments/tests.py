from decimal import Decimal
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from users.models import User, MechanicProfile
from vehicles.models import Vehicle
from breakdowns.models import Breakdown
from .models import Payment

class PayGatePaymentAPITests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            username="paygate_client",
            email="paygate_client@example.com",
            password="Password123",
            telephone="+2250101010199",
            role="USAGER"
        )
        self.mechanic_user = User.objects.create_user(
            username="paygate_mechanic",
            email="paygate_mechanic@example.com",
            password="Password123",
            telephone="+2250707070799",
            role="MECANICIEN"
        )
        MechanicProfile.objects.create(
            user=self.mechanic_user,
            specialite="Climatisation & Moteur",
            garage_name="Garage Ivoire",
            latitude=5.3500,
            longitude=-4.0300,
            est_disponible=True
        )
        self.vehicle = Vehicle.objects.create(
            owner=self.client_user,
            make="Peugeot",
            model="308",
            license_plate="1111-XX-01"
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
            description="Panne de demarreur"
        )
        self.payment = self.breakdown.payment

    @patch('payments.views.initiate_paygate_payment')
    def test_initiate_paygate_payment(self, mock_paygate):
        mock_paygate.return_value = {
            'status': 0,
            'tx_reference': 'PAYGATE-REF-12345'
        }
        initiate_url = reverse('payment-initiate', kwargs={'pk': self.payment.id})
        data = {
            "phone_number": "90123456",
            "network": "TMONEY"
        }
        response = self.client_api.post(initiate_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.phone_number, "90123456")
        self.assertEqual(self.payment.network, "TMONEY")
        # Status remains PENDING until webhook confirms
        self.assertEqual(self.payment.status, 'PENDING')
        self.assertEqual(self.payment.paygate_tx_reference, 'PAYGATE-REF-12345')

    def test_paygate_webhook_success(self):
        webhook_url = reverse('paygate-webhook')
        payload = {
            "identifier": str(self.payment.id),
            "tx_reference": "PAYGATE-TX-SUCCESS-99",
            "status": 0
        }
        response = self.client_api.post(webhook_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'HELD_IN_ESCROW')
        self.assertEqual(self.payment.paygate_tx_reference, "PAYGATE-TX-SUCCESS-99")
        self.assertEqual(self.payment.transaction_reference, "PAYGATE-TX-SUCCESS-99")

    def test_confirm_release_transfers_90_percent_to_mechanic(self):
        # 1. Put payment in HELD_IN_ESCROW
        self.payment.status = 'HELD_IN_ESCROW'
        self.payment.save()

        release_url = reverse('payment-confirm-release', kwargs={'pk': self.payment.id})

        # 2. Attempt release while breakdown is PENDING -> fail
        response = self.client_api.post(release_url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Mechanic completes breakdown
        self.breakdown.mechanic = self.mechanic_user
        self.breakdown.status = 'COMPLETED'
        self.breakdown.save()

        # 4. Client confirms release
        response = self.client_api.post(release_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'RELEASED')
        self.assertEqual(self.payment.platform_commission, Decimal('300.00')) # 10%
        self.assertEqual(self.payment.mechanic_payout, Decimal('2700.00'))     # 90%

        # 5. Mechanic cannot release (Client only permission check)
        unauth_response = self.mechanic_api.post(release_url)
        self.assertEqual(unauth_response.status_code, status.HTTP_403_FORBIDDEN)
