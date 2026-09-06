from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import Payment
from .serializers import PaymentSerializer
from .paygate import initiate_paygate_payment

class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', '') == 'MECANICIEN':
            return Payment.objects.all()
        return Payment.objects.filter(user=user)

    @action(detail=True, methods=['post'], url_path='initiate')
    def initiate(self, request, pk=None):
        payment = self.get_object()

        phone_number = request.data.get('phone_number')
        network = request.data.get('network')

        if not phone_number or not network:
            return Response(
                {"error": "Veuillez fournir un numéro de téléphone ('phone_number') et le réseau ('network': TMONEY ou FLOOZ)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if network not in ['TMONEY', 'FLOOZ']:
            return Response(
                {"error": "Le réseau doit être TMONEY ou FLOOZ."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Enregistre le numéro et le réseau sans modifier le statut (qui reste PENDING)
        payment.phone_number = phone_number
        payment.network = network
        payment.save()

        # Déclenche l'API PayGate v1
        paygate_res = initiate_paygate_payment(payment, phone_number, network)

        if paygate_res.get('status') == 0 and paygate_res.get('tx_reference'):
            payment.paygate_tx_reference = paygate_res.get('tx_reference')
            payment.save()

        serializer = self.get_serializer(payment)
        return Response(
            {
                "message": "Demande de paiement PayGate envoyée avec succès.",
                "paygate_response": paygate_res,
                "payment": serializer.data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='confirm-release')
    def confirm_release(self, request, pk=None):
        payment = self.get_object()

        # Seul le client propriétaire du paiement ou un admin peut libérer les fonds
        if request.user != payment.user and not request.user.is_staff:
            return Response(
                {"error": "Seul le client ayant effectué la demande peut libérer les fonds."},
                status=status.HTTP_403_FORBIDDEN
            )

        breakdown = payment.breakdown

        if breakdown.status != 'COMPLETED':
            return Response(
                {"error": f"La libération des fonds requiert le statut COMPLETED pour la panne. Statut actuel: '{breakdown.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if payment.status != 'HELD_IN_ESCROW':
            return Response(
                {"error": f"Seul un paiement sous séquestre (HELD_IN_ESCROW) peut être libéré. Statut actuel: '{payment.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Transfert 90% au mécanicien, conserve 10% pour la plateforme MecaLink
        payment.status = 'RELEASED'
        payment.save()

        serializer = self.get_serializer(payment)
        return Response(
            {
                "message": f"Fonds libérés avec succès ! Payout mécanicien: {payment.mechanic_payout} XOF (90%), Commission plateforme MecaLink: {payment.platform_commission} XOF (10%).",
                "payment": serializer.data
            },
            status=status.HTTP_200_OK
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def paygate_webhook(request):
    """
    Webhook appelé de manière asynchrone par PayGate Global lors de la confirmation d'un paiement.
    Payload: { "tx_reference": "...", "status": 0, "identifier": "..." }
    """
    data = request.data
    identifier = data.get('identifier')
    tx_ref = data.get('tx_reference')
    paygate_status = data.get('status')

    if not identifier:
        return Response({"error": "Paramètre 'identifier' manquant."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        payment = Payment.objects.get(id=identifier)
    except Payment.DoesNotExist:
        return Response({"error": f"Paiement #{identifier} introuvable."}, status=status.HTTP_404_NOT_FOUND)

    # Si status PayGate == 0 (Succès)
    if str(paygate_status) == '0' or paygate_status == 0:
        payment.status = 'HELD_IN_ESCROW'
        if tx_ref:
            payment.paygate_tx_reference = tx_ref
            payment.transaction_reference = tx_ref
        payment.save()
        return Response({
            "message": "Webhook PayGate traité avec succès. Paiement sous séquestre.",
            "payment_id": payment.id,
            "status": payment.status
        }, status=status.HTTP_200_OK)

    return Response({
        "message": f"Webhook reçu avec statut PayGate {paygate_status}.",
        "payment_id": payment.id,
        "status": payment.status
    }, status=status.HTTP_200_OK)
