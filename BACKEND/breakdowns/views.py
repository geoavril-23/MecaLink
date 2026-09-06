from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Breakdown
from .serializers import BreakdownSerializer
from .utils import haversine_distance

class BreakdownViewSet(viewsets.ModelViewSet):
    serializer_class = BreakdownSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # Si c'est un mécanicien ou admin, on montre toutes les pannes
        # Sinon, on filtre pour ne montrer que les pannes du client connecté
        if user.is_staff or getattr(user, 'role', '') == 'MECANICIEN':
            return Breakdown.objects.all()
        return Breakdown.objects.filter(client=user)

    def perform_create(self, serializer):
        # Assigne automatiquement le client authentifié
        serializer.save(client=self.request.user)

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """
        Récupère toutes les pannes en attente d'intervention.
        Filtre facultatif par rayon d'action (lat, lon, radius en km).
        """
        pending_breakdowns = Breakdown.objects.filter(status='PENDING')
        
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius = request.query_params.get('radius')

        if lat is not None and lon is not None:
            try:
                lat_f = float(lat)
                lon_f = float(lon)
                radius_f = float(radius) if radius is not None else None

                breakdowns_with_dist = []
                for b in pending_breakdowns:
                    dist = haversine_distance(lat_f, lon_f, b.latitude, b.longitude)
                    if dist is not None:
                        if radius_f is None or dist <= radius_f:
                            breakdowns_with_dist.append((dist, b))

                # Tri par distance croissante
                breakdowns_with_dist.sort(key=lambda x: x[0])
                pending_breakdowns = [b for dist, b in breakdowns_with_dist]
            except ValueError:
                pass

        serializer = self.get_serializer(pending_breakdowns, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch', 'post'], url_path='accept')
    def accept(self, request, pk=None):
        breakdown = self.get_object()
        
        if getattr(request.user, 'role', '') != 'MECANICIEN' and not request.user.is_staff:
            return Response(
                {"error": "Seuls les mécaniciens peuvent accepter des pannes."},
                status=status.HTTP_403_FORBIDDEN
            )

        if breakdown.status != 'PENDING':
            return Response(
                {"error": "Cette panne a déjà été prise en charge ou annulée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Assigne le mécanicien connecté et met à jour le statut
        breakdown.mechanic = request.user
        breakdown.status = 'ACCEPTED'
        breakdown.save()

        serializer = self.get_serializer(breakdown)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch', 'post'], url_path='in-progress')
    def in_progress(self, request, pk=None):
        breakdown = self.get_object()

        if breakdown.status != 'ACCEPTED':
            return Response(
                {"error": "La panne doit être dans l'état ACCEPTED pour passer en cours."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if breakdown.mechanic != request.user and not request.user.is_staff:
            return Response(
                {"error": "Vous n'êtes pas le mécanicien assigné à cette intervention."},
                status=status.HTTP_403_FORBIDDEN
            )

        breakdown.status = 'IN_PROGRESS'
        breakdown.save()

        serializer = self.get_serializer(breakdown)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch', 'post'], url_path='complete')
    def complete(self, request, pk=None):
        breakdown = self.get_object()

        if breakdown.status != 'IN_PROGRESS':
            return Response(
                {"error": "La panne doit être dans l'état IN_PROGRESS pour être terminée."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if breakdown.mechanic != request.user and not request.user.is_staff:
            return Response(
                {"error": "Vous n'êtes pas le mécanicien assigné à cette intervention."},
                status=status.HTTP_403_FORBIDDEN
            )

        breakdown.status = 'COMPLETED'
        breakdown.save()

        serializer = self.get_serializer(breakdown)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['patch', 'post'], url_path='cancel')
    def cancel(self, request, pk=None):
        breakdown = self.get_object()

        if breakdown.status == 'COMPLETED':
            return Response(
                {"error": "Impossible d'annuler une panne déjà terminée."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Seul le client, le mécanicien assigné ou un admin peut annuler
        if request.user != breakdown.client and request.user != breakdown.mechanic and not request.user.is_staff:
            return Response(
                {"error": "Vous n'avez pas l'autorisation d'annuler cette panne."},
                status=status.HTTP_403_FORBIDDEN
            )

        breakdown.status = 'CANCELLED'
        breakdown.save()

        serializer = self.get_serializer(breakdown)
        return Response(serializer.data, status=status.HTTP_200_OK)