from django.db.models import Avg
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from breakdowns.models import Breakdown
from users.models import User
from .models import Evaluation
from .serializers import EvaluationSerializer

class EvaluationViewSet(viewsets.ModelViewSet):
    serializer_class = EvaluationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', '') == 'MECANICIEN':
            return Evaluation.objects.all()
        return Evaluation.objects.filter(client=user)

    def create(self, request, *args, **kwargs):
        breakdown_id = request.data.get('breakdown')
        rating = request.data.get('rating')
        comment = request.data.get('comment', '')

        if not breakdown_id or rating is None:
            return Response(
                {"error": "Veuillez fournir 'breakdown' et 'rating' (note entre 1 et 5)."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError()
        except ValueError:
            return Response(
                {"error": "La note 'rating' doit être un nombre entier compris entre 1 et 5."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            breakdown = Breakdown.objects.get(id=breakdown_id)
        except Breakdown.DoesNotExist:
            return Response(
                {"error": f"Panne #{breakdown_id} introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        # 1. Seul le client ayant créé la panne peut donner un avis
        if request.user != breakdown.client:
            return Response(
                {"error": "Seul le client à l'origine du signalement peut évaluer cette prestation."},
                status=status.HTTP_403_FORBIDDEN
            )

        # 2. Vérification que la panne est COMPLETED
        if breakdown.status != 'COMPLETED':
            return Response(
                {"error": f"Seule une panne avec le statut 'COMPLETED' peut être évaluée. Statut actuel: '{breakdown.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Vérification du paiement libéré (RELEASED)
        if not hasattr(breakdown, 'payment') or breakdown.payment.status != 'RELEASED':
            return Response(
                {"error": "L'évaluation requiert un paiement entièrement libéré ('RELEASED')."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Vérification qu'aucune évaluation n'existe déjà pour cette panne
        if hasattr(breakdown, 'evaluation'):
            return Response(
                {"error": "Une évaluation a déjà été soumise pour cette intervention."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not breakdown.mechanic:
            return Response(
                {"error": "Aucun mécanicien n'est associé à cette panne."},
                status=status.HTTP_400_BAD_REQUEST
            )

        evaluation = Evaluation.objects.create(
            breakdown=breakdown,
            client=request.user,
            mechanic=breakdown.mechanic,
            rating=rating,
            comment=comment
        )

        serializer = self.get_serializer(evaluation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='mechanic/(?P<mechanic_id>[^/.]+)')
    def mechanic_evaluations(self, request, mechanic_id=None):
        try:
            mechanic = User.objects.get(id=mechanic_id, role='MECANICIEN')
        except User.DoesNotExist:
            return Response(
                {"error": f"Mécanicien #{mechanic_id} introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        evaluations = Evaluation.objects.filter(mechanic=mechanic)
        avg_rating = evaluations.aggregate(Avg('rating'))['rating__avg']
        avg_rating = round(avg_rating, 2) if avg_rating is not None else 0.0

        serializer = self.get_serializer(evaluations, many=True)
        return Response(
            {
                "mechanic_id": mechanic.id,
                "mechanic_username": mechanic.username,
                "average_rating": avg_rating,
                "total_evaluations": evaluations.count(),
                "evaluations": serializer.data
            },
            status=status.HTTP_200_OK
        )
