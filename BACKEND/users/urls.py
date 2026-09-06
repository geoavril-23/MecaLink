from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import (
    RegisterView,
    MechanicProfileUpdateView,
    AvailableMechanicsListView
)

urlpatterns = [
    # Authentification & Comptes
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profil & Liste Mécaniciens
    path('mechanic/profile/', MechanicProfileUpdateView.as_view(), name='mechanic_profile_update'),
    path('mechanics/available/', AvailableMechanicsListView.as_view(), name='available_mechanics_list'),
]