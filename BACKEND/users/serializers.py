from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from .models import User, MechanicProfile


class MechanicProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = MechanicProfile
        fields = ['specialite', 'garage_name', 'latitude', 'longitude', 'est_disponible']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    
    # Ajout des validateurs d'unicité pour bloquer les doublons au niveau de DRF
    username = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), 
                message="Ce nom d'utilisateur existe déjà."
            )
        ]
    )
    telephone = serializers.CharField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(), 
                message="Ce numéro de téléphone est déjà utilisé."
            )
        ]
    )
    
    mechanic_profile = MechanicProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'telephone', 'role', 'password', 'mechanic_profile']

    def create(self, validated_data):
        profile_data = validated_data.pop('mechanic_profile', None)

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            telephone=validated_data['telephone'],
            role=validated_data.get('role', User.ROLE_CHOICES[0][0]),
            password=validated_data['password']
        )

        if user.role == 'MECANICIEN' and profile_data:
            MechanicProfile.objects.create(user=user, **profile_data)

        return user


class MechanicProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = MechanicProfile
        fields = ['specialite', 'garage_name', 'latitude', 'longitude', 'est_disponible']


class MechanicListSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username')
    telephone = serializers.CharField(source='user.telephone')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = MechanicProfile
        fields = ['id', 'username', 'telephone', 'email', 'specialite', 'garage_name', 'latitude', 'longitude', 'est_disponible']