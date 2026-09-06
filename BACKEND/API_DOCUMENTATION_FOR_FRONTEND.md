# MecaLink — API Documentation for Frontend Team

> **Base URL (développement local):** `http://localhost:8000`
> **Format:** Toutes les requêtes et réponses utilisent `Content-Type: application/json`.

---

## Authentification

Tous les endpoints protégés nécessitent l'en-tête suivant :

```
Authorization: Bearer <access_token>
```

Le token est obtenu via `/api/users/login/`. Sa durée de vie est courte ; utiliser `/api/users/token/refresh/` pour le renouveler.

---

## 1. Auth & Utilisateurs

### `POST /api/users/register/`
Inscription d'un usager ou d'un mécanicien.

**Requête — Usager :**
```json
{
  "username": "jean_dupont",
  "email": "jean@example.com",
  "telephone": "+2250101234567",
  "role": "USAGER",
  "password": "MonMotDePasse123"
}
```

**Requête — Mécanicien :**
```json
{
  "username": "meca_paul",
  "email": "paul@example.com",
  "telephone": "+2250709876543",
  "role": "MECANICIEN",
  "password": "MonMotDePasse123",
  "mechanic_profile": {
    "specialite": "Moteur & Freinage",
    "garage_name": "Garage AutoPro",
    "latitude": 5.3485,
    "longitude": -4.0305,
    "est_disponible": true
  }
}
```

**Réponse `201 Created` :**
```json
{
  "message": "Compte créé avec succès !",
  "user": {
    "id": 1,
    "username": "jean_dupont",
    "email": "jean@example.com",
    "telephone": "+2250101234567",
    "role": "USAGER"
  }
}
```

---

### `POST /api/users/login/`
Connexion et récupération des tokens JWT.

**Requête :**
```json
{
  "username": "jean_dupont",
  "password": "MonMotDePasse123"
}
```

**Réponse `200 OK` :**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

---

### `POST /api/users/token/refresh/`
Renouvellement du token d'accès.

**Requête :**
```json
{ "refresh": "<refresh_token>" }
```

**Réponse `200 OK` :**
```json
{ "access": "<nouveau_access_token>" }
```

---

### `PUT /api/users/mechanic/profile/` 🔒
Mise à jour du profil mécanicien connecté.

**Requête :**
```json
{
  "specialite": "Climatisation & Électronique",
  "garage_name": "Nouveau Garage",
  "latitude": 5.3600,
  "longitude": -4.0100,
  "est_disponible": false
}
```

**Réponse `200 OK` :**
```json
{
  "message": "Profil mis à jour avec succès !",
  "profile": {
    "specialite": "Climatisation & Électronique",
    "garage_name": "Nouveau Garage",
    "latitude": 5.3600,
    "longitude": -4.0100,
    "est_disponible": false
  }
}
```

---

### `GET /api/users/mechanics/available/` 🔒
Liste des mécaniciens disponibles.

**Réponse `200 OK` :**
```json
[
  {
    "id": 2,
    "username": "meca_paul",
    "telephone": "+2250709876543",
    "email": "paul@example.com",
    "specialite": "Moteur & Freinage",
    "garage_name": "Garage AutoPro",
    "latitude": 5.3485,
    "longitude": -4.0305,
    "est_disponible": true
  }
]
```

---

## 2. Véhicules

### `GET /api/vehicles/` 🔒
Liste les véhicules de l'usager connecté.

**Réponse `200 OK` :**
```json
[
  {
    "id": 1,
    "make": "Toyota",
    "model": "Corolla",
    "year": 2020,
    "license_plate": "1234-AB-01",
    "color": "Gris",
    "created_at": "2026-09-06T10:00:00Z"
  }
]
```

---

### `POST /api/vehicles/` 🔒
Ajouter un véhicule.

**Requête :**
```json
{
  "make": "Toyota",
  "model": "Corolla",
  "year": 2020,
  "license_plate": "1234-AB-01",
  "color": "Gris"
}
```

**Réponse `201 Created` :**
```json
{
  "id": 1,
  "make": "Toyota",
  "model": "Corolla",
  "year": 2020,
  "license_plate": "1234-AB-01",
  "color": "Gris",
  "created_at": "2026-09-06T10:00:00Z"
}
```

---

### `DELETE /api/vehicles/{id}/` 🔒
Supprime un véhicule de l'usager. **Réponse `204 No Content`.**

---

## 3. Pannes (Breakdowns)

### `POST /api/breakdowns/` 🔒
Signaler une panne.

**Requête :**
```json
{
  "vehicle": 1,
  "latitude": 5.3400,
  "longitude": -4.0300,
  "description": "Batterie à plat au carrefour du Plateau"
}
```

**Réponse `201 Created` :**
```json
{
  "id": 10,
  "client": 1,
  "client_username": "jean_dupont",
  "mechanic": null,
  "mechanic_username": null,
  "vehicle": 1,
  "vehicle_details": "Toyota Corolla (1234-AB-01)",
  "latitude": 5.3400,
  "longitude": -4.0300,
  "description": "Batterie à plat au carrefour du Plateau",
  "status": "PENDING",
  "distance_km": null,
  "created_at": "2026-09-06T10:05:00Z",
  "updated_at": "2026-09-06T10:05:00Z"
}
```

---

### `GET /api/breakdowns/pending/?lat=5.35&lon=-4.03&radius=10` 🔒
Liste les pannes en attente dans un rayon (km). Triées par proximité. Utilisé par les mécaniciens.

**Paramètres de requête (optionnels) :**
| Paramètre | Type   | Description              |
|-----------|--------|--------------------------|
| `lat`     | float  | Latitude du mécanicien   |
| `lon`     | float  | Longitude du mécanicien  |
| `radius`  | float  | Rayon de recherche en km |

**Réponse `200 OK` :**
```json
[
  {
    "id": 10,
    "client_username": "jean_dupont",
    "vehicle_details": "Toyota Corolla (1234-AB-01)",
    "latitude": 5.3400,
    "longitude": -4.0300,
    "description": "Batterie à plat au carrefour du Plateau",
    "status": "PENDING",
    "distance_km": 1.25,
    "created_at": "2026-09-06T10:05:00Z"
  }
]
```

> **Navigation :** Construire le lien "Y aller" avec :
> `https://www.google.com/maps/dir/?api=1&destination={latitude},{longitude}`

---

### `PATCH /api/breakdowns/{id}/accept/` 🔒
Un mécanicien accepte la panne.

**Réponse `200 OK` :** Objet Breakdown avec `status: "ACCEPTED"` et `mechanic` renseigné.

---

### `PATCH /api/breakdowns/{id}/in-progress/` 🔒
Marquer la panne en cours d'intervention.

**Réponse `200 OK` :** Objet Breakdown avec `status: "IN_PROGRESS"`.

---

### `PATCH /api/breakdowns/{id}/complete/` 🔒
Marquer la panne comme terminée.

**Réponse `200 OK` :** Objet Breakdown avec `status: "COMPLETED"`.

---

### `PATCH /api/breakdowns/{id}/cancel/` 🔒
Annuler une panne. Accessible au client ou au mécanicien assigné.

**Réponse `200 OK` :** Objet Breakdown avec `status: "CANCELLED"`.

---

## 4. Paiements

### `POST /api/payments/{id}/initiate/` 🔒
Déclencher le paiement Mobile Money via PayGate.

**Requête :**
```json
{
  "phone_number": "90123456",
  "network": "TMONEY"
}
```
> `network` accepte : `TMONEY` ou `FLOOZ`

**Réponse `200 OK` :**
```json
{
  "message": "Demande de paiement PayGate envoyée avec succès.",
  "paygate_response": {
    "status": 0,
    "tx_reference": "PAYGATE-REF-12345"
  },
  "payment": {
    "id": 3,
    "breakdown_id": 10,
    "phone_number": "90123456",
    "network": "TMONEY",
    "total_amount": "3000.00",
    "platform_commission": "300.00",
    "mechanic_payout": "2700.00",
    "status": "PENDING",
    "paygate_tx_reference": "PAYGATE-REF-12345"
  }
}
```

---

### `POST /api/payments/paygate-webhook/`
Endpoint appelé automatiquement par PayGate Global après confirmation du paiement côté opérateur. **Pas d'en-tête `Authorization` requis.**

**Payload PayGate :**
```json
{
  "tx_reference": "PAYGATE-REF-12345",
  "status": 0,
  "identifier": "3"
}
```
> `status == 0` = Succès → Payment passe en `HELD_IN_ESCROW`.

**Réponse `200 OK` :**
```json
{
  "message": "Webhook PayGate traité avec succès. Paiement sous séquestre.",
  "payment_id": 3,
  "status": "HELD_IN_ESCROW"
}
```

---

### `POST /api/payments/{id}/confirm-release/` 🔒
Le client libère les fonds après la fin de l'intervention.

**Pré-requis :** `breakdown.status == "COMPLETED"` et `payment.status == "HELD_IN_ESCROW"`.

**Réponse `200 OK` :**
```json
{
  "message": "Fonds libérés avec succès ! Payout mécanicien: 2700.00 XOF (90%), Commission plateforme MecaLink: 300.00 XOF (10%).",
  "payment": {
    "id": 3,
    "status": "RELEASED",
    "mechanic_payout": "2700.00",
    "platform_commission": "300.00"
  }
}
```

---

## 5. Interventions

### `POST /api/interventions/start/` 🔒
Le mécanicien démarre l'intervention sur le lieu de la panne.

**Requête :**
```json
{ "breakdown": 10 }
```

**Réponse `201 Created` :**
```json
{
  "message": "Intervention démarrée avec succès !",
  "intervention": {
    "id": 5,
    "breakdown": 10,
    "breakdown_id": 10,
    "mechanic": 2,
    "mechanic_username": "meca_paul",
    "client_username": "jean_dupont",
    "start_time": "2026-09-06T10:30:00Z",
    "end_time": null,
    "status": "IN_PROGRESS",
    "diagnostic_notes": null,
    "parts_replaced": []
  }
}
```

---

### `PATCH /api/interventions/{id}/complete/` 🔒
Marquer l'intervention comme terminée avec les notes techniques.

**Requête :**
```json
{
  "diagnostic_notes": "Remplacement batterie 12V et nettoyage des cosses.",
  "parts_replaced": ["Batterie 12V", "Cosses de batterie"]
}
```

**Réponse `200 OK` :**
```json
{
  "message": "Intervention et panne marquées comme COMPLETED avec succès !",
  "intervention": {
    "id": 5,
    "status": "COMPLETED",
    "end_time": "2026-09-06T11:15:00Z",
    "diagnostic_notes": "Remplacement batterie 12V et nettoyage des cosses.",
    "parts_replaced": ["Batterie 12V", "Cosses de batterie"]
  }
}
```

---

## 6. Évaluations

### `POST /api/evaluations/` 🔒
Le client note le mécanicien après une intervention terminée et un paiement libéré.

**Pré-requis :** `breakdown.status == "COMPLETED"` ET `payment.status == "RELEASED"`.

**Requête :**
```json
{
  "breakdown": 10,
  "rating": 5,
  "comment": "Rapide et professionnel, je recommande !"
}
```

**Réponse `201 Created` :**
```json
{
  "id": 1,
  "breakdown": 10,
  "client": 1,
  "client_username": "jean_dupont",
  "mechanic": 2,
  "mechanic_username": "meca_paul",
  "rating": 5,
  "comment": "Rapide et professionnel, je recommande !",
  "created_at": "2026-09-06T11:30:00Z"
}
```

---

### `GET /api/evaluations/mechanic/{mechanic_id}/` 🔒
Liste des avis et note moyenne d'un mécanicien.

**Réponse `200 OK` :**
```json
{
  "mechanic_id": 2,
  "mechanic_username": "meca_paul",
  "average_rating": 4.75,
  "total_evaluations": 12,
  "evaluations": [
    {
      "id": 1,
      "rating": 5,
      "comment": "Rapide et professionnel !",
      "client_username": "jean_dupont",
      "created_at": "2026-09-06T11:30:00Z"
    }
  ]
}
```

---

## Statuts & Codes HTTP de Référence

| Code | Signification         |
|------|-----------------------|
| 200  | Succès                |
| 201  | Créé avec succès      |
| 204  | Supprimé (No Content) |
| 400  | Données invalides     |
| 401  | Non authentifié       |
| 403  | Accès interdit        |
| 404  | Ressource introuvable |

## Cycle de Vie d'une Panne

```
PENDING → ACCEPTED → IN_PROGRESS → COMPLETED
                  ↘           ↘
                CANCELLED   CANCELLED
```

## Cycle de Vie d'un Paiement

```
PENDING → (initiate + webhook PayGate) → HELD_IN_ESCROW → (confirm-release) → RELEASED
                                                        ↘
                                                      REFUNDED / FAILED
```
