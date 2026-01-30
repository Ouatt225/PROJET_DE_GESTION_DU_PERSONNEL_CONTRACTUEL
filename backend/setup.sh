#!/bin/bash

echo "========================================"
echo "Configuration du backend EmpManager"
echo "========================================"
echo ""

echo "1. Création de l'environnement virtuel..."
python3 -m venv venv
source venv/bin/activate

echo ""
echo "2. Installation des dépendances..."
pip install -r requirements.txt

echo ""
echo "3. Application des migrations..."
python manage.py makemigrations
python manage.py migrate

echo ""
echo "4. Création du superutilisateur..."
echo ""
echo "Utilisateurs de démonstration :"
echo "- Admin: admin / admin123"
echo "- Manager: manager / manager123"
echo "- Employé: employee / employee123"
echo ""

python manage.py shell <<EOF
from django.contrib.auth.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@empmanager.com', 'admin123')

if not User.objects.filter(username='manager').exists():
    User.objects.create_user('manager', 'manager@empmanager.com', 'manager123', is_staff=True)

if not User.objects.filter(username='employee').exists():
    User.objects.create_user('employee', 'employee@empmanager.com', 'employee123')

print('Utilisateurs créés avec succès!')
EOF

echo ""
echo "========================================"
echo "Configuration terminée avec succès!"
echo "========================================"
echo ""
echo "Pour démarrer le serveur, exécutez :"
echo "python manage.py runserver"
echo ""
