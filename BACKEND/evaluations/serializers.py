from rest_framework import serializers
from .models import Evaluation

class EvaluationSerializer(serializers.ModelSerializer):
    client_username = serializers.ReadOnlyField(source='client.username')
    mechanic_username = serializers.ReadOnlyField(source='mechanic.username')

    class Meta:
        model = Evaluation
        fields = [
            'id', 'breakdown', 'client', 'client_username', 
            'mechanic', 'mechanic_username', 'rating', 
            'comment', 'created_at'
        ]
        read_only_fields = ['id', 'client', 'mechanic', 'created_at']
