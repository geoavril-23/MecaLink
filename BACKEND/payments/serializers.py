from rest_framework import serializers
from .models import Payment

class PaymentSerializer(serializers.ModelSerializer):
    breakdown_id = serializers.ReadOnlyField(source='breakdown.id')
    user_email = serializers.ReadOnlyField(source='user.email')

    class Meta:
        model = Payment
        fields = [
            'id', 'breakdown_id', 'user_email', 'phone_number', 'network',
            'base_fee', 'distance_fee', 'total_amount', 'platform_commission', 
            'mechanic_payout', 'status', 'paygate_tx_reference', 'transaction_reference', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['total_amount', 'platform_commission', 'mechanic_payout', 'status', 'created_at', 'updated_at']
