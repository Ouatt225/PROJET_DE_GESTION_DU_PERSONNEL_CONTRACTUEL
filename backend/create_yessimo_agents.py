"""
Script pour creer les comptes des 23 agents YESSIMO.
Entreprise: YESSIMO | Poste: Ouvrier
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empmanager.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Department, Employee, PasswordRecord
from api.encryption import encrypt_password

# Recuperer le departement YESSIMO
try:
    yessimo = Department.objects.get(name='YESSIMO')
    print(f"Entreprise trouvee : {yessimo.name} (ID: {yessimo.id})")
except Department.DoesNotExist:
    print("ERREUR : L'entreprise YESSIMO n'existe pas. Creation...")
    yessimo = Department.objects.create(name='YESSIMO', description='Groupe Yessimo')
    print(f"Entreprise creee : {yessimo.name} (ID: {yessimo.id})")

# Liste des 23 agents YESSIMO
agents = [
    {'nom': 'BOHOUSSOU', 'prenom': 'Attien Armande', 'service': 'INSPECT GENERAL', 'matricule': '980448-M', 'sexe': 'female'},
    {'nom': 'BOKA', 'prenom': 'Roselyne', 'service': 'DR DAOUKRO', 'matricule': '202108-H', 'sexe': 'female'},
    {'nom': 'GOKON LOU', 'prenom': "N'Tromble Estelle", 'service': 'DD TIASSALE', 'matricule': '201028-C', 'sexe': 'female'},
    {'nom': 'FETE', 'prenom': 'Adjoua Justine', 'service': 'DDPE', 'matricule': '202226-Z', 'sexe': 'female'},
    {'nom': 'KRA', 'prenom': 'Adjoua Virginie', 'service': 'DR ABIDJAN', 'matricule': '201024-Y', 'sexe': 'female'},
    {'nom': 'MOROKO', 'prenom': 'Berenger Aymar', 'service': 'DD LAKOTA', 'matricule': '202509-I', 'sexe': 'male'},
    {'nom': 'ZAN LOU', 'prenom': 'Beyan Clarisse', 'service': 'DD OUME', 'matricule': '202513-M', 'sexe': 'female'},
    {'nom': 'DALOUGOU', 'prenom': 'Bedio Ange Rodrigue', 'service': 'DD LAKOTA', 'matricule': '201822-V', 'sexe': 'male'},
    {'nom': 'GBRA', 'prenom': 'Sagouhi Leaticia', 'service': 'DRAGP', 'matricule': '202506-F', 'sexe': 'female'},
    {'nom': 'KOUAME', 'prenom': 'Yao Innocent', 'service': 'DD BLOLEQUIN', 'matricule': '201829-C', 'sexe': 'male'},
    {'nom': 'N\'DRE ABO', 'prenom': 'Vincent De Paul', 'service': 'DRH', 'matricule': '202143-R', 'sexe': 'male'},
    {'nom': 'OUATTARA', 'prenom': 'Konzieda', 'service': 'DR BONDOUKOU', 'matricule': '200925-Y', 'sexe': 'male'},
    {'nom': 'KOUASSI', 'prenom': 'Kouadio', 'service': 'DD M\'BAHIAKRO', 'matricule': '202515-O', 'sexe': 'male'},
    {'nom': 'GUIKAHUIE', 'prenom': 'Waze Estelle Epse Nemlin', 'service': 'DD GRAND BASSAM', 'matricule': '2020507-G', 'sexe': 'female'},
    {'nom': 'TRAORE', 'prenom': 'Abdoulaye', 'service': 'DAFP', 'matricule': '200095-P', 'sexe': 'male'},
    {'nom': 'OUATTARA', 'prenom': 'Aramatou Epse Gnapi', 'service': 'DD GRAND BASSAM', 'matricule': '202514-N', 'sexe': 'female'},
    {'nom': 'DEI', 'prenom': 'Emeline', 'service': 'DD JACQUEVILLE', 'matricule': '201011-L', 'sexe': 'female'},
    {'nom': 'KOFFI', 'prenom': 'Akoumian', 'service': 'DRH', 'matricule': '202508-H', 'sexe': 'female'},
    {'nom': 'IRIO KOSIA', 'prenom': 'Kra Odette', 'service': 'DGIR', 'matricule': '201815-O', 'sexe': 'female'},
    {'nom': 'BOLI', 'prenom': 'Erica Patricia', 'service': 'DGIR', 'matricule': '201816-P', 'sexe': 'female'},
    {'nom': 'TRAORE', 'prenom': 'Seguetio', 'service': 'DD BOUNDIALI', 'matricule': '202512-L', 'sexe': 'female'},
    {'nom': 'BEUGRE', 'prenom': 'Bassy Jean Michel', 'service': 'DAFP', 'matricule': '202425-Y', 'sexe': 'male'},
    {'nom': 'YAO', 'prenom': 'Kossia Yamine Catherine', 'service': 'DD ABIDJAN', 'matricule': '201021-V', 'sexe': 'female'},
]

def generate_username(prenom, nom, existing_usernames):
    """Genere un username unique au format prenom.nom"""
    first = prenom.split()[0].lower().replace("'", "").replace("-", "")
    last = nom.split()[0].lower().replace("'", "").replace("-", "")
    username = f"{first}.{last}"
    # Gerer les doublons
    if username in existing_usernames:
        i = 2
        while f"{username}{i}" in existing_usernames:
            i += 1
        username = f"{username}{i}"
    return username

def generate_password(nom, index):
    """Genere un mot de passe au format Yess@Xxxx00"""
    clean_nom = nom.split()[0].replace("'", "").replace("-", "")
    prefix = clean_nom[:4].capitalize()
    return f"Yess@{prefix}{index:02d}"

print("=" * 70)
print("CREATION DES 23 COMPTES AGENTS YESSIMO")
print("=" * 70)

existing_usernames = set(User.objects.values_list('username', flat=True))
created = 0
skipped = 0

for idx, agent in enumerate(agents, 1):
    username = generate_username(agent['prenom'], agent['nom'], existing_usernames)
    password = generate_password(agent['nom'], idx)

    # Verifier si l'utilisateur existe deja
    if User.objects.filter(username=username).exists():
        print(f"  [{idx:2d}] DEJA EXISTANT : {username}")
        skipped += 1
        continue

    # Creer l'utilisateur Django
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=agent['prenom'],
        last_name=agent['nom'],
        email=f"{username}@yessimo.ci",
        is_staff=False,
        is_superuser=False
    )

    # Creer le profil employe
    Employee.objects.create(
        user=user,
        first_name=agent['prenom'],
        last_name=agent['nom'],
        email=f"{username}@yessimo.ci",
        department=yessimo,
        direction=agent['service'],
        position='Ouvrier',
        hire_date='2025-12-01',
        matricule=agent['matricule'],
        gender=agent['sexe'],
        status='active'
    )

    # Sauvegarder le mot de passe dans PasswordRecord
    PasswordRecord.objects.update_or_create(
        user=user,
        defaults={
            'password_encrypted': encrypt_password(password),
            'role': 'employee',
        }
    )

    existing_usernames.add(username)
    created += 1
    print(f"  [{idx:2d}] {agent['nom']} {agent['prenom']}")
    print(f"       Username: {username} | Password: {password} | Service: {agent['service']}")

print(f"\n{'=' * 70}")
print(f"RESULTAT : {created} comptes crees, {skipped} ignores (deja existants)")
print(f"{'=' * 70}")
