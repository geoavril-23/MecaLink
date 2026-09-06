from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PaymentViewSet, paygate_webhook

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payment')

urlpatterns = [
    path('paygate-webhook/', paygate_webhook, name='paygate-webhook'),
    path('', include(router.urls)),
]
