from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from .models import MechanicProfile
from .serializers import (
    UserRegistrationSerializer,
    MechanicProfileUpdateSerializer,
    MechanicListSerializer
)

class RegisterView(APIView):
    """
    Inscription d'un utilisateur (Usager ou Mécanicien)
    """
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Compte créé avec succès !",
                    "user": serializer.data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MechanicProfileUpdateView(APIView):
    """
    Mise à jour du profil par le mécanicien connecté
    """
    permission_classes = [IsAuthenticated]

    def put(self, request):
        if request.user.role != 'MECANICIEN':
            return Response(
                {"error": "Seuls les mécaniciens peuvent accéder à cette fonctionnalité."},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            profile = request.user.mechanic_profile
        except MechanicProfile.DoesNotExist:
            return Response(
                {"error": "Profil mécanicien introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MechanicProfileUpdateSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profil mis à jour avec succès !",
                "profile": serializer.data
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AvailableMechanicsListView(APIView):
    """
    Liste des mécaniciens disponibles pour les usagers
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        available_mechanics = MechanicProfile.objects.filter(est_disponible=True)
        serializer = MechanicListSerializer(available_mechanics, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)