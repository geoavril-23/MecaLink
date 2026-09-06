from rest_framework import serializers
from .models import Intervention

class InterventionSerializer(serializers.ModelSerializer):
    breakdown_id = serializers.ReadOnlyField(source='breakdown.id')
    mechanic_username = serializers.ReadOnlyField(source='mechanic.username')
    client_username = serializers.ReadOnlyField(source='breakdown.client.username')

    class Meta:
        model = Intervention
        fields = [
            'id', 'breakdown', 'breakdown_id', 'mechanic', 'mechanic_username', 
            'client_username', 'start_time', 'end_time', 'status', 
            'diagnostic_notes', 'parts_replaced', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'mechanic', 'start_time', 'end_time', 'status', 'created_at', 'updated_at']
