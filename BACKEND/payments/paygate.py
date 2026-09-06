import requests
from django.conf import settings

def initiate_paygate_payment(payment, phone_number, network):
    """Initiates a PayGate mobile payment (T-Money/Flooz)."""
    payload = {
        'auth_token': settings.PAYGATE_API_KEY,
        'phone_number': phone_number,
        'amount': float(payment.total_amount),
        'description': f"Depannage MecaLink #{payment.breakdown.id}",
        'identifier': str(payment.id),
        'network': network
    }

    if not getattr(settings, 'PAYGATE_LIVE_MODE', True):
        return {'status': 0, 'tx_reference': f"MOCK_TX_{payment.id}"}

    try:
        response = requests.post(
            getattr(settings, 'PAYGATE_INITIATE_URL', 'https://paygateglobal.com/api/v1/pay'),
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        return response.json()
    except Exception as e:
        return {'status': -1, 'error': str(e)}
