# Backend EmpManager - API Django REST

## Description

Backend pour l'application de gestion du personnel EmpManager. Cette API REST est construite avec Django et Django REST Framework, utilise PostgreSQL comme base de données et implémente l'authentification JWT.

## Fonctionnalités

- **Authentification JWT** : Connexion sécurisée avec tokens JWT
- **Gestion des employés** : CRUD complet pour les employés
- **Gestion des départements/entreprises** : CRUD pour les départements
- **Gestion des congés** : Demandes, approbations et rejets de congés
- **Gestion des présences** : Suivi du pointage quotidien des employés
- **Rôles utilisateurs** : Admin, Manager et Employé
- **API RESTful** : Endpoints documentés et cohérents

## Prérequis

- Python 3.10+
- PostgreSQL 12+
- pip (gestionnaire de paquets Python)

## Installation

### 1. Créer un environnement virtuel

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 3. Configurer PostgreSQL

Créez une base de données PostgreSQL :

```sql
CREATE DATABASE empmanager_db;
CREATE USER postgres WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE empmanager_db TO postgres;
```

### 4. Configurer les variables d'environnement

Copiez le fichier `.env.example` en `.env` et modifiez les valeurs :

```bash
cp .env.example .env
```

Modifiez le fichier `.env` avec vos informations :

```
SECRET_KEY=votre-cle-secrete-unique
DEBUG=True
DB_NAME=empmanager_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
DB_HOST=localhost
DB_PORT=5432
```

### 5. Appliquer les migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Créer un super utilisateur

```bash
python manage.py createsuperuser
```

Suivez les instructions pour créer votre compte administrateur.

### 7. Charger les données de démonstration (optionnel)

```bash
python manage.py loaddata fixtures/initial_data.json
```

### 8. Lancer le serveur

```bash
python manage.py runserver
```

L'API sera disponible sur : `http://localhost:8000/`

## Structure du projet

```
backend/
│
├── empmanager/          # Configuration du projet Django
│   ├── settings.py      # Paramètres Django
│   ├── urls.py          # URLs principales
│   └── wsgi.py          # Configuration WSGI
│
├── api/                 # Application API
│   ├── models.py        # Modèles de données
│   ├── serializers.py   # Serializers DRF
│   ├── views.py         # Views et ViewSets
│   ├── urls.py          # URLs de l'API
│   └── admin.py         # Configuration admin Django
│
├── manage.py            # Script de gestion Django
├── requirements.txt     # Dépendances Python
└── README.md            # Ce fichier
```

## Endpoints API

### Authentification

- `POST /api/auth/login/` - Connexion (username, password, role)
- `POST /api/auth/register/` - Inscription
- `POST /api/token/` - Obtenir token JWT
- `POST /api/token/refresh/` - Rafraîchir token

### Départements

- `GET /api/departments/` - Liste des départements
- `POST /api/departments/` - Créer un département
- `GET /api/departments/{id}/` - Détails d'un département
- `PUT /api/departments/{id}/` - Mettre à jour un département
- `DELETE /api/departments/{id}/` - Supprimer un département
- `GET /api/departments/{id}/employees/` - Employés d'un département

### Employés

- `GET /api/employees/` - Liste des employés
- `POST /api/employees/` - Créer un employé
- `GET /api/employees/{id}/` - Détails d'un employé
- `PUT /api/employees/{id}/` - Mettre à jour un employé
- `DELETE /api/employees/{id}/` - Supprimer un employé
- `GET /api/employees/by_department/` - Employés groupés par département

### Congés

- `GET /api/leaves/` - Liste des congés
- `POST /api/leaves/` - Créer une demande de congé
- `GET /api/leaves/{id}/` - Détails d'une demande
- `PUT /api/leaves/{id}/` - Mettre à jour une demande
- `DELETE /api/leaves/{id}/` - Supprimer une demande
- `POST /api/leaves/{id}/approve/` - Approuver une demande
- `POST /api/leaves/{id}/reject/` - Rejeter une demande
- `GET /api/leaves/pending/` - Demandes en attente

### Présences

- `GET /api/attendances/` - Liste des présences
- `POST /api/attendances/` - Créer un pointage
- `GET /api/attendances/{id}/` - Détails d'un pointage
- `PUT /api/attendances/{id}/` - Mettre à jour un pointage
- `DELETE /api/attendances/{id}/` - Supprimer un pointage
- `GET /api/attendances/today/` - Présences du jour
- `GET /api/attendances/by_employee/?employee_id={id}` - Présences par employé

### Dashboard

- `GET /api/dashboard/stats/` - Statistiques du tableau de bord

## Modèles de données

### Department (Département)
- `name` : Nom du département
- `manager` : Responsable
- `description` : Description

### Employee (Employé)
- `first_name`, `last_name` : Nom et prénom
- `email` : Email (unique)
- `phone` : Téléphone
- `department` : Département (FK)
- `position` : Poste
- `hire_date` : Date d'embauche
- `salary` : Salaire
- `cnps` : Numéro CNPS
- `address` : Adresse
- `status` : Statut (active, inactive, on_leave)

### Leave (Congé)
- `employee` : Employé (FK)
- `leave_type` : Type (paid, sick, unpaid, parental, other)
- `start_date`, `end_date` : Dates de début et fin
- `reason` : Raison
- `status` : Statut (pending, approved, rejected)
- `approved_by` : Approuvé par (User FK)

### Attendance (Présence)
- `employee` : Employé (FK)
- `date` : Date
- `check_in`, `check_out` : Heures d'entrée et sortie
- `status` : Statut (present, absent, late, half-day)
- `notes` : Notes

## Authentification

L'API utilise JWT (JSON Web Tokens) pour l'authentification. Pour accéder aux endpoints protégés :

1. Obtenez un token avec `/api/auth/login/`
2. Incluez le token dans les headers :
   ```
   Authorization: Bearer <votre_token>
   ```

## Admin Django

Accédez à l'interface d'administration Django sur :
`http://localhost:8000/admin/`

Utilisez les identifiants du super utilisateur créé.

## Tests

```bash
python manage.py test
```

## Production

Pour le déploiement en production :

1. Définissez `DEBUG=False` dans `.env`
2. Changez `SECRET_KEY` par une valeur unique et sécurisée
3. Configurez `ALLOWED_HOSTS` avec votre domaine
4. Utilisez un serveur WSGI comme Gunicorn
5. Configurez un reverse proxy (Nginx)
6. Activez HTTPS
7. Configurez les fichiers statiques

## Support

Pour toute question ou problème, consultez la documentation Django :
- https://docs.djangoproject.com/
- https://www.django-rest-framework.org/
