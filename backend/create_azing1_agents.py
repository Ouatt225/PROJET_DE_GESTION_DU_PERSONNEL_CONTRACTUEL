"""
Script pour creer les comptes des 63 agents AZING 1 (Secretaires).
Entreprise: AZING 1 | Poste: Secretaire
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empmanager.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Department, Employee, PasswordRecord

# Recuperer le departement AZING 1
try:
    azing1 = Department.objects.get(name='AZING 1')
    print(f"Entreprise trouvee : {azing1.name} (ID: {azing1.id})")
except Department.DoesNotExist:
    print("ERREUR : L'entreprise AZING 1 n'existe pas. Creation...")
    azing1 = Department.objects.create(name='AZING 1', description='AZING IVOIR Sarl - Lot 2 Secretaires')
    print(f"Entreprise creee : {azing1.name} (ID: {azing1.id})")

agents = [
    {'nom': 'ABISSA', 'prenom': 'Akoua', 'matricule': '3609-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Agboville', 'sexe': 'female'},
    {'nom': 'ADJOUMANI', 'prenom': 'Abonan Virginie', 'matricule': '3610-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'AKE', 'prenom': 'Choh Marilyn', 'matricule': '3611-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'AMLE', 'prenom': 'Nora', 'matricule': '3612-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'ANOUGBA', 'prenom': 'Bosson P.M', 'matricule': '3614-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Daoukro', 'sexe': 'male'},
    {'nom': 'ASSEU', 'prenom': 'Kousso Florence', 'matricule': '3615-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Bouake', 'sexe': 'female'},
    {'nom': 'ATTRON', 'prenom': 'Tenah Adelaide', 'matricule': '3616-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'BEDA', 'prenom': 'Sophie', 'matricule': '3617-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Grand-Bassam', 'sexe': 'female'},
    {'nom': 'BENE', 'prenom': 'Tamea Anastasie', 'matricule': '3618-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Agnibilekro', 'sexe': 'female'},
    {'nom': 'BEUGRE', 'prenom': 'Wrolo Marina P', 'matricule': '3619-ME', 'fonction': 'Dactylographe', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'BOLI', 'prenom': 'Koudouho Rachelle', 'matricule': '3620-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'CHI N\'CHO', 'prenom': 'Micheline', 'matricule': '3621-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'COULIBALY', 'prenom': 'Mahoua C', 'matricule': '3622-ME', 'fonction': 'Dactylographe', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'COULIBALY', 'prenom': 'nee Sow D', 'matricule': '3623-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Bouake', 'sexe': 'female'},
    {'nom': 'DAFLAN', 'prenom': 'Annick Romaine', 'matricule': '3624-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'DEDJI', 'prenom': 'Dohouri Eliane', 'matricule': '3625-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Daoukro', 'sexe': 'female'},
    {'nom': 'DIA LOU', 'prenom': 'Golenan P', 'matricule': '3626-ME', 'fonction': 'Dactylographe', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'DIARRA', 'prenom': 'Kaffougoutio A', 'matricule': '3627-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'DIOMANDE', 'prenom': 'Fatoumata', 'matricule': '3628-ME', 'fonction': 'Dactylographe', 'lieu': 'Man', 'sexe': 'female'},
    {'nom': 'DRUIDE', 'prenom': 'Ismaelle Mylene', 'matricule': '3629-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Duekoue', 'sexe': 'female'},
    {'nom': 'EBE', 'prenom': 'Bomo Vanessa C', 'matricule': '3630-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Agnibilekro', 'sexe': 'female'},
    {'nom': 'EPONOU', 'prenom': 'Ama Marina', 'matricule': '3631-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Tiassale', 'sexe': 'female'},
    {'nom': 'GUETAPE', 'prenom': 'Kongne S', 'matricule': '3633-ME', 'fonction': 'Secretaire de direction', 'lieu': 'San-Pedro', 'sexe': 'female'},
    {'nom': 'KANGA', 'prenom': 'Amenan Louise', 'matricule': '3634-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'KAREKE', 'prenom': 'nee Esmel L', 'matricule': '3635-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'KOFFI', 'prenom': 'Affoumani Eric', 'matricule': '3637-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Bongouanou', 'sexe': 'male'},
    {'nom': 'KOFFI', 'prenom': 'Allangba J', 'matricule': '3638-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Yamoussoukro', 'sexe': 'male'},
    {'nom': 'KOFFI', 'prenom': 'Kouame Patrice', 'matricule': '3639-ME', 'fonction': 'Dactylographe', 'lieu': 'Guiglo', 'sexe': 'male'},
    {'nom': 'KOKO', 'prenom': 'Aman Achile', 'matricule': '3640-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Abidjan', 'sexe': 'male'},
    {'nom': 'KONAN', 'prenom': 'nee Yao Aya A', 'matricule': '3641-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'KONE', 'prenom': 'Nakathala Olga', 'matricule': '3642-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'KOUADIO', 'prenom': 'Yao Adaman', 'matricule': '3644-ME', 'fonction': 'Secretaire', 'lieu': 'Abidjan', 'sexe': 'male'},
    {'nom': 'KOUAMENAN', 'prenom': 'Anoh A', 'matricule': '3645-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Soubre', 'sexe': 'male'},
    {'nom': 'KOUASSI', 'prenom': 'Adja Lucie', 'matricule': '3646-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'KOUASSI', 'prenom': 'Adjoua H', 'matricule': '3647-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'KOUASSI', 'prenom': 'Kouakou Joel', 'matricule': '3648-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Tiassale', 'sexe': 'male'},
    {'nom': 'KOUASSI', 'prenom': "N'Goa Chris", 'matricule': '3649-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Toulepleu', 'sexe': 'male'},
    {'nom': 'KOUASSI', 'prenom': 'Tchuneboi B.P', 'matricule': '3650-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Grand Bassam', 'sexe': 'male'},
    {'nom': 'LOGBO', 'prenom': 'Affoue Yvonne', 'matricule': '3651-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': "N'DOLI", 'prenom': 'Tanoh Ama S', 'matricule': '3653-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': "N'GUESSAN", 'prenom': 'Viviane I', 'matricule': '3656-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'RABE', 'prenom': 'Akale Corine F', 'matricule': '3657-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Gagnoa', 'sexe': 'female'},
    {'nom': 'SAMAKE', 'prenom': 'Sita', 'matricule': '3658-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'SAMASSI', 'prenom': 'Mariam', 'matricule': '3659-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Odienne', 'sexe': 'female'},
    {'nom': 'SEKA', 'prenom': 'Gakouo Sandrine', 'matricule': '3660-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Adzope', 'sexe': 'female'},
    {'nom': 'SIE', 'prenom': 'Aya Sylvie Bertille B', 'matricule': '3661-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'SIGNO', 'prenom': 'Flora Nadine', 'matricule': '3662-ME', 'fonction': 'Dactylographe', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'SINARE', 'prenom': 'Bintou', 'matricule': '3663-ME', 'fonction': 'Dactylographe', 'lieu': 'Bangolo', 'sexe': 'female'},
    {'nom': 'SOME', 'prenom': 'Hensha Pysca M', 'matricule': '3664-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Gagnoa', 'sexe': 'female'},
    {'nom': 'SOUMAHORO', 'prenom': 'Togba H', 'matricule': '3665-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Vavoua', 'sexe': 'female'},
    {'nom': 'TAI', 'prenom': 'Axel Ingrid Felicite', 'matricule': '3666-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Dabou', 'sexe': 'female'},
    {'nom': 'TAN', 'prenom': 'Irene M. epse D', 'matricule': '3667-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'TOURE', 'prenom': 'Kariata', 'matricule': '3668-ME', 'fonction': 'Secretaire dactylographe', 'lieu': 'Bouake', 'sexe': 'female'},
    {'nom': 'TRAORE', 'prenom': 'Fanta', 'matricule': '3669-ME', 'fonction': 'Secretaire', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'TRAORE', 'prenom': 'Fatoumata', 'matricule': '3670-ME', 'fonction': 'Secretaire de direction', 'lieu': 'Abidjan', 'sexe': 'female'},
    {'nom': 'GOGBE', 'prenom': 'Golou Pelagie', 'matricule': '3672-ME', 'fonction': 'Secretaire', 'lieu': 'Bouake', 'sexe': 'female'},
    {'nom': 'SIE', 'prenom': 'Marie Solange', 'matricule': '4007-ME', 'fonction': 'Secretaire', 'lieu': 'Beoumi', 'sexe': 'female'},
    {'nom': 'KOUYATE', 'prenom': 'Francoise', 'matricule': '4008-ME', 'fonction': 'Secretaire', 'lieu': 'Daloa', 'sexe': 'female'},
    {'nom': 'GBASSE', 'prenom': 'Bouaffou Andree', 'matricule': '4009-ME', 'fonction': 'Secretaire', 'lieu': 'Bondoukou', 'sexe': 'female'},
    {'nom': 'LIGBET', 'prenom': 'Alix Tatiana', 'matricule': '5155-ME', 'fonction': 'Secretaire', 'lieu': 'Katiola', 'sexe': 'female'},
    {'nom': 'KONAN', 'prenom': 'Affoue Angele', 'matricule': '5156-ME', 'fonction': 'Secretaire', 'lieu': 'Mankono', 'sexe': 'female'},
    {'nom': 'YEO', 'prenom': 'Nalourou Deborah', 'matricule': '5157-ME', 'fonction': 'Secretaire', 'lieu': 'Seguela', 'sexe': 'female'},
    {'nom': 'KOTO', 'prenom': 'Ange Felicite', 'matricule': '5158-ME', 'fonction': 'Secretaire', 'lieu': 'Abidjan', 'sexe': 'female'},
]

def generate_username(prenom, nom, existing_usernames):
    first = prenom.split()[0].lower().replace("'", "").replace("-", "").replace(".", "")
    last = nom.split()[0].lower().replace("'", "").replace("-", "").replace(".", "")
    # Retirer le mot "nee" si present
    if first == 'nee':
        parts = prenom.split()
        first = parts[1].lower().replace("'", "").replace("-", "").replace(".", "") if len(parts) > 1 else parts[0].lower()
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
    return f"Azin@{prefix}{index:02d}"

print("=" * 70)
print("CREATION DES 63 COMPTES AGENTS AZING 1 (SECRETAIRES)")
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
        email=f"{username}@azing-ivoir.ci",
        is_staff=False,
        is_superuser=False
    )

    Employee.objects.create(
        user=user,
        first_name=agent['prenom'],
        last_name=agent['nom'],
        email=f"{username}@azing-ivoir.ci",
        department=azing1,
        direction=agent['lieu'],
        position='Secretaire',
        hire_date='2025-12-01',
        matricule=agent['matricule'],
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
    print(f"       Username: {username} | Password: {password} | Lieu: {agent['lieu']}")

print(f"\n{'=' * 70}")
print(f"RESULTAT : {created} comptes crees, {skipped} ignores")
print(f"{'=' * 70}")
