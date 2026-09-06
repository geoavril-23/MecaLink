from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from breakdowns.models import Breakdown
from .models import Intervention
from .serializers import InterventionSerializer

class InterventionViewSet(viewsets.ModelViewSet):
    serializer_class = InterventionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or getattr(user, 'role', '') == 'MECANICIEN':
            return Intervention.objects.all()
        return Intervention.objects.filter(breakdown__client=user)

    @action(detail=False, methods=['post'], url_path='start')
    def start_intervention(self, request):
        user = request.user
        if getattr(user, 'role', '') != 'MECANICIEN' and not user.is_staff:
            return Response(
                {"error": "Seuls les mécaniciens peuvent démarrer une intervention."},
                status=status.HTTP_403_FORBIDDEN
            )

        breakdown_id = request.data.get('breakdown')
        if not breakdown_id:
            return Response(
                {"error": "Le paramètre 'breakdown' est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            breakdown = Breakdown.objects.get(id=breakdown_id)
        except Breakdown.DoesNotExist:
            return Response(
                {"error": f"Panne #{breakdown_id} introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        if hasattr(breakdown, 'intervention'):
            return Response(
                {"error": "Une intervention existe déjà pour cette panne."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if breakdown.status not in ['PENDING', 'ACCEPTED']:
            return Response(
                {"error": f"Impossible de démarrer une intervention sur une panne avec le statut '{breakdown.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Met à jour la panne avec le mécanicien connecté et le statut IN_PROGRESS
        breakdown.mechanic = user
        breakdown.status = 'IN_PROGRESS'
        breakdown.save()

        # Crée l'intervention
        intervention = Intervention.objects.create(
            breakdown=breakdown,
            mechanic=user,
            status='IN_PROGRESS'
        )

        serializer = self.get_serializer(intervention)
        return Response(
            {
                "message": "Intervention démarrée avec succès !",
                "intervention": serializer.data
            },
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['patch', 'post'], url_path='complete')
    def complete_intervention(self, request, pk=None):
        intervention = self.get_object()

        if intervention.mechanic != request.user and not request.user.is_staff:
            return Response(
                {"error": "Vous n'êtes pas le mécanicien assigné à cette intervention."},
                status=status.HTTP_403_FORBIDDEN
            )

        if intervention.status != 'IN_PROGRESS':
            return Response(
                {"error": f"Seule une intervention 'IN_PROGRESS' peut être terminée. Statut actuel: '{intervention.status}'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        notes = request.data.get('diagnostic_notes', intervention.diagnostic_notes)
        parts = request.data.get('parts_replaced', intervention.parts_replaced)

        intervention.diagnostic_notes = notes
        intervention.parts_replaced = parts
        intervention.status = 'COMPLETED'
        intervention.end_time = timezone.now()
        intervention.save()

        # Met à jour le statut de la panne liée à COMPLETED
        breakdown = intervention.breakdown
        breakdown.status = 'COMPLETED'
        breakdown.save()

        serializer = self.get_serializer(intervention)
        return Response(
            {
                "message": "Intervention et panne marquées comme COMPLETED avec succès !",
                "intervention": serializer.data
            },
            status=status.HTTP_200_OK
        )
