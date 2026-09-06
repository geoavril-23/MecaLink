from rest_framework import serializers
from .models import Breakdown
from .utils import haversine_distance

class BreakdownSerializer(serializers.ModelSerializer):
    distance_km = serializers.SerializerMethodField()
    client_username = serializers.CharField(source='client.username', read_only=True)
    mechanic_username = serializers.CharField(source='mechanic.username', read_only=True)
    vehicle_details = serializers.SerializerMethodField()

    class Meta:
        model = Breakdown
        fields = [
            'id', 'client', 'client_username', 'mechanic', 'mechanic_username',
            'vehicle', 'vehicle_details', 'latitude', 'longitude', 'description',
            'status', 'distance_km', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'client', 'mechanic', 'status', 'created_at', 'updated_at']

    def get_distance_km(self, obj):
        request = self.context.get('request')
        if request:
            lat = request.query_params.get('lat')
            lon = request.query_params.get('lon')
            if lat is not None and lon is not None:
                return haversine_distance(lat, lon, obj.latitude, obj.longitude)
        return None

    def get_vehicle_details(self, obj):
        if obj.vehicle:
            return f"{obj.vehicle.make} {obj.vehicle.model} ({obj.vehicle.license_plate})"
        return None