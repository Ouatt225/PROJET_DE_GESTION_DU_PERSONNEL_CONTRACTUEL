"""
Script pour creer les comptes des 25 agents IVOIR GARDIENNAGE (Vigiles).
Entreprise: IVOIR GARDIENNAGE | Poste: Vigile
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empmanager.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Department, Employee, PasswordRecord

try:
    ig = Department.objects.get(name='IVOIR GARDIENNAGE')
    print(f"Entreprise trouvee : {ig.name} (ID: {ig.id})")
except Department.DoesNotExist:
    print("ERREUR : L'entreprise IVOIR GARDIENNAGE n'existe pas. Creation...")
    ig = Department.objects.create(name='IVOIR GARDIENNAGE', description='Ivoir Gardiennage - Vigiles')
    print(f"Entreprise creee : {ig.name} (ID: {ig.id})")

agents = [
    {'nom': 'ADINGRA', 'prenom': 'Koffi Adjoumani', 'service': 'DD TANDA', 'sexe': 'male'},
    {'nom': 'AGNINI', 'prenom': 'Aboya Brou', 'service': 'DD AGNIBILEKRO', 'sexe': 'male'},
    {'nom': 'AKAFFOU', 'prenom': 'Brou Mesmin', 'service': 'DDPE ABIDJAN', 'sexe': 'male'},
    {'nom': 'AKOURA', 'prenom': 'Kouame Adjoumani', 'service': 'DD TANDA', 'sexe': 'male'},
    {'nom': 'BINDE', 'prenom': 'Kouakou', 'service': 'DR ABENGOUROU', 'sexe': 'male'},
    {'nom': 'BOTCHE', 'prenom': 'Boguitche', 'service': 'DR ABENGOUROU', 'sexe': 'male'},
    {'nom': 'COULIBALY', 'prenom': 'Fona', 'service': 'DR KORHOGO', 'sexe': 'male'},
    {'nom': 'DIARRASSOUBA', 'prenom': 'Abou', 'service': 'DD DABAKALA', 'sexe': 'male'},
    {'nom': 'DIOMANDE', 'prenom': 'Losseni', 'service': 'DD VAVOUA', 'sexe': 'male'},
    {'nom': 'DOUMBIA', 'prenom': 'Abou', 'service': 'DD LAKOTA', 'sexe': 'male'},
    {'nom': 'FLINDE', 'prenom': 'Yode Jean Marc', 'service': 'DR GAGNOA', 'sexe': 'male'},
    {'nom': 'TONHETONNE', 'prenom': 'Yemalin Paela Patrice', 'service': 'GD ABIDJAN', 'sexe': 'male'},
    {'nom': 'GOHOUN', 'prenom': 'Boli Gbaka', 'service': 'DD DABOU', 'sexe': 'male'},
    {'nom': 'GUEI', 'prenom': 'Blesson Jean Marie', 'service': 'DD YOPOUGON', 'sexe': 'male'},
    {'nom': 'IRIDIE', 'prenom': 'Bi Gore Alexis', 'service': 'DD SINFRA', 'sexe': 'male'},
    {'nom': 'KANGA', 'prenom': 'Kouassi Jerome', 'service': 'DR BOUAFLE', 'sexe': 'male'},
    {'nom': 'KOUADIO', 'prenom': 'Kouame Celestin', 'service': 'DD TOUMODI', 'sexe': 'male'},
    {'nom': 'KOUAKOU', 'prenom': 'Kouame Firmin', 'service': 'DR ABENGOUROU', 'sexe': 'male'},
    {'nom': 'KOUAME', 'prenom': 'Kouakou Olivier', 'service': 'DR DALOA', 'sexe': 'male'},
    {'nom': 'KOUASSI', 'prenom': 'Gblan Pascal Aime', 'service': 'DDPE ABIDJAN', 'sexe': 'male'},
    {'nom': "N'GOUAN", 'prenom': 'Augustin Mathieu', 'service': 'DPE ABIDJAN', 'sexe': 'male'},
    {'nom': 'GOUDE', 'prenom': 'Djety Emmanuel', 'service': "DD M'BAHIAKRO", 'sexe': 'male'},
    {'nom': 'DONGO', 'prenom': 'Amouan Evelyne', 'service': 'DG ABIDJAN', 'sexe': 'female'},
    {'nom': 'TOULAUD', 'prenom': 'Noel', 'service': 'DD DABOU', 'sexe': 'male'},
    {'nom': 'YEBOUA', 'prenom': 'K. Adjoumani', 'service': 'DR BONDOUKOU', 'sexe': 'male'},
]

def generate_username(prenom, nom, existing_usernames):
    first = prenom.split()[0].lower().replace("'", "").replace("-", "").replace(".", "")
    last = nom.split()[0].lower().replace("'", "").replace("-", "").replace(".", "")
    username = f"{first}.{last}"
    if username in existing_usernames:
        i = 2
        while f"{username}{i}" in existing_usernames:
            i += 1
        username = f"{username}{i}"
    return username

def generate_password(nom, index):
    clean_nom = nom.split()[0].replace("'", "").replace("-", "")
    prefix = clean_nom[:4].capitalize()
    return f"Ivoi@{prefix}{index:02d}"

print("=" * 70)
print("CREATION DES 25 COMPTES AGENTS IVOIR GARDIENNAGE (VIGILES)")
print("=" * 70)

existing_usernames = set(User.objects.values_list('username', flat=True))
created = 0
skipped = 0

for idx, agent in enumerate(agents, 1):
    username = generate_username(agent['prenom'], agent['nom'], existing_usernames)
    password = generate_password(agent['nom'], idx)

    if User.objects.filter(username=username).exists():
        print(f"  [{idx:2d}] DEJA EXISTANT : {username}")
        skipped += 1
        continue

    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=agent['prenom'],
        last_name=agent['nom'],
        email=f"{username}@ivoirgardiennage.ci",
        is_staff=False,
        is_superuser=False
    )

    Employee.objects.create(
        user=user,
        first_name=agent['prenom'],
        last_name=agent['nom'],
        email=f"{username}@ivoirgardiennage.ci",
        department=ig,
        direction=agent['service'],
        position='Vigile',
        hire_date='2025-12-01',
        gender=agent['sexe'],
        status='active'
    )

    PasswordRecord.objects.update_or_create(
        user=user,
        defaults={
            'password_plain': password,
            'role': 'employee',
        }
    )

    existing_usernames.add(username)
    created += 1
    print(f"  [{idx:2d}] {agent['nom']} {agent['prenom']}")
    print(f"       Username: {username} | Password: {password} | Service: {agent['service']}")

print(f"\n{'=' * 70}")
print(f"RESULTAT : {created} comptes crees, {skipped} ignores")
print(f"{'=' * 70}")
