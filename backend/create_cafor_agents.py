"""
Script pour creer les comptes des 62 agents CAFOR (Chauffeurs).
Entreprise: CAFOR | Poste: Chauffeur
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empmanager.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Department, Employee, PasswordRecord

try:
    cafor = Department.objects.get(name='CAFOR')
    print(f"Entreprise trouvee : {cafor.name} (ID: {cafor.id})")
except Department.DoesNotExist:
    print("ERREUR : L'entreprise CAFOR n'existe pas. Creation...")
    cafor = Department.objects.create(name='CAFOR', description='Centre Autonome de Formation de Recyclage et de Prestations')
    print(f"Entreprise creee : {cafor.name} (ID: {cafor.id})")

agents = [
    {'nom': 'AGUIE', 'prenom': 'Yapo Bertin', 'service': 'DD BONGOUANOU', 'sexe': 'male'},
    {'nom': 'AHOUTOU', 'prenom': "N'Guessan M", 'service': 'DD SAKASSOU', 'sexe': 'male'},
    {'nom': 'ALIKO', 'prenom': 'Okobe Okobe Tresor', 'service': 'CABINET', 'sexe': 'male'},
    {'nom': 'AMOA', 'prenom': 'Brou Favier', 'service': 'DTIR TANDA', 'sexe': 'male'},
    {'nom': 'AMON', 'prenom': 'Kouassi Date', 'service': 'DD ABIDJAN', 'sexe': 'male'},
    {'nom': 'ARDJOUAMA', 'prenom': 'Sidi Kevin', 'service': 'DR ABENGOUROU', 'sexe': 'male'},
    {'nom': 'BEDA', 'prenom': 'Brou Maleu Romaric', 'service': 'DR DIVO', 'sexe': 'male'},
    {'nom': 'BESSE', 'prenom': 'Christian Akre Henri', 'service': 'DGIR', 'sexe': 'male'},
    {'nom': 'CAMARA', 'prenom': 'Yacouba', 'service': 'DTIR DABAKALA', 'sexe': 'male'},
    {'nom': 'CISSE', 'prenom': 'Yacouba', 'service': 'DR ABOISSO', 'sexe': 'male'},
    {'nom': 'COULIBALY', 'prenom': 'Drissa', 'service': 'DAEP', 'sexe': 'male'},
    {'nom': 'DADIE', 'prenom': 'Danon Clovis', 'service': 'DTIR SAKASSOU', 'sexe': 'male'},
    {'nom': 'DEUH', 'prenom': 'Gonmin Gregoire', 'service': 'DR GUIGLO', 'sexe': 'male'},
    {'nom': 'DIENGBEU', 'prenom': 'Carlos', 'service': 'DR GAGNOA', 'sexe': 'male'},
    {'nom': 'DJE', 'prenom': 'Koffi Leon', 'service': 'DR DIMBOKRO', 'sexe': 'male'},
    {'nom': 'DJE', 'prenom': 'Kouame Faustin', 'service': 'DGIRQ', 'sexe': 'male'},
    {'nom': 'DOSSO', 'prenom': 'Ali Hassane', 'service': 'DR TOUBA', 'sexe': 'male'},
    {'nom': 'DOU', 'prenom': 'Yannick', 'service': 'DD ABIDJAN', 'sexe': 'male'},
    {'nom': 'DOUMBIA', 'prenom': 'Ibrahima', 'service': 'DDR ODIENNE', 'sexe': 'male'},
    {'nom': 'ETTOU', 'prenom': 'Manouan Bosson Armand', 'service': 'DR YAMOUSSOUKRO', 'sexe': 'male'},
    {'nom': 'GANON', 'prenom': 'Moussa', 'service': 'DD MANKONO', 'sexe': 'male'},
    {'nom': 'GBA', 'prenom': 'Gnaoue Raphael', 'service': 'DR AGBOVILLE', 'sexe': 'male'},
    {'nom': 'GOKALE', 'prenom': 'Toffe Jacques', 'service': 'INSP-GENERAL', 'sexe': 'male'},
    {'nom': 'GUESSAN', 'prenom': 'Gnalla Gilbert', 'service': 'DD ADIAKE', 'sexe': 'male'},
    {'nom': 'KABRAN', 'prenom': 'Desiree Arielle Armande', 'service': 'INSP GLE', 'sexe': 'female'},
    {'nom': 'KAKOU', 'prenom': 'Monet Hilaire', 'service': 'DR ADZOPE', 'sexe': 'male'},
    {'nom': 'KOBENAN', 'prenom': 'Abdel Kader', 'service': 'DR ABIDJAN', 'sexe': 'male'},
    {'nom': 'KOBRI', 'prenom': 'Edoukou Augustin', 'service': 'DR ABENGOUROU', 'sexe': 'male'},
    {'nom': 'KOFFI', 'prenom': 'Kouassi Jean Christophe', 'service': 'DAFP', 'sexe': 'male'},
    {'nom': 'KOFFI', 'prenom': "N'Dri Bernardin", 'service': 'Grd-LAHOU', 'sexe': 'male'},
    {'nom': 'KONATE', 'prenom': 'Yssouf', 'service': 'CABINET', 'sexe': 'male'},
    {'nom': 'KONE', 'prenom': 'Adama', 'service': 'BONDOUKOU', 'sexe': 'male'},
    {'nom': 'KONE', 'prenom': 'Adama', 'service': 'DR ODIENNE', 'sexe': 'male'},
    {'nom': 'KOFFI', 'prenom': 'Koffi Elisee', 'service': 'DPE', 'sexe': 'male'},
    {'nom': 'KONE', 'prenom': 'Mamadou', 'service': 'DR DAOUKRO', 'sexe': 'male'},
    {'nom': 'KONE', 'prenom': 'Souleymane', 'service': 'DR ABIDJAN', 'sexe': 'male'},
    {'nom': 'KOUADIO', 'prenom': 'Adolphe', 'service': 'CABINET', 'sexe': 'male'},
    {'nom': 'KODIO', 'prenom': 'Olive-Aubin', 'service': 'DAFP', 'sexe': 'male'},
    {'nom': 'KOUADJO', 'prenom': 'Ehounou Tano', 'service': 'DR BOUAFLE', 'sexe': 'male'},
    {'nom': 'KOUAME', 'prenom': 'Jean Oscar', 'service': 'DD ABIDJAN', 'sexe': 'male'},
    {'nom': 'KOUASSI', 'prenom': 'Brou Germain', 'service': 'DR AGBOVILLE', 'sexe': 'male'},
    {'nom': 'KOUASSI', 'prenom': 'Koffi Nestor', 'service': 'DD ISSIA', 'sexe': 'male'},
    {'nom': 'KOUASSI', 'prenom': 'Yacouba Ouattara', 'service': 'Grd-LAHOU', 'sexe': 'male'},
    {'nom': 'KOUROUMA', 'prenom': 'Mory', 'service': 'DD BEOUMI', 'sexe': 'male'},
    {'nom': 'MONHIRO', 'prenom': 'Tiehoulo Arnaud', 'service': 'DD TOULEPLEU', 'sexe': 'male'},
    {'nom': 'MOUROUFIE', 'prenom': 'Koffi Narcisse', 'service': 'DD AGNIBILEKRO', 'sexe': 'male'},
    {'nom': 'NEMLIN', 'prenom': 'Richard', 'service': 'DRH', 'sexe': 'male'},
    {'nom': "N'GAZA", 'prenom': 'Marc Orel', 'service': 'DGIRQ', 'sexe': 'male'},
    {'nom': 'OKARA', 'prenom': 'Kokola Jean Eudes', 'service': 'DRH', 'sexe': 'male'},
    {'nom': 'OUATTARA', 'prenom': 'Amoro', 'service': 'DD LAKOTA', 'sexe': 'male'},
    {'nom': 'OUATTARA', 'prenom': 'Siaka', 'service': 'DD SAKASSOU', 'sexe': 'male'},
    {'nom': 'OULAI', 'prenom': 'Tablemon Ferdinand', 'service': 'DD LAKOTA', 'sexe': 'male'},
    {'nom': 'SANOGO', 'prenom': 'Syndou', 'service': 'DD TIASSALE', 'sexe': 'male'},
    {'nom': 'SERGES', 'prenom': 'Bernabe Monney', 'service': "DD M'BAHIAKRO", 'sexe': 'male'},
    {'nom': 'SOUMAHORO', 'prenom': 'Adama', 'service': 'DD G-BASSAM', 'sexe': 'male'},
    {'nom': 'TANOH', 'prenom': 'Toussaint de Bettie', 'service': 'SD FORMATION', 'sexe': 'male'},
    {'nom': 'TAYE', 'prenom': 'Koudou Dominique', 'service': 'DAFP', 'sexe': 'male'},
    {'nom': 'TIMITE', 'prenom': 'Charles', 'service': 'DR AGBOVILLE', 'sexe': 'male'},
    {'nom': 'TOURE', 'prenom': 'Yao', 'service': 'DD VAVOUA', 'sexe': 'male'},
    {'nom': 'VEH', 'prenom': 'Louh Olivier', 'service': 'DR BOUAKE', 'sexe': 'male'},
    {'nom': 'YOU', 'prenom': 'Tizie Marc-Antoine', 'service': 'DR SEGUELA', 'sexe': 'male'},
    {'nom': 'ZOUNIN', 'prenom': 'Bi Trazie', 'service': 'DR S-PEDRO', 'sexe': 'male'},
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
    return f"Cafo@{prefix}{index:02d}"

print("=" * 70)
print("CREATION DES 62 COMPTES AGENTS CAFOR (CHAUFFEURS)")
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
        email=f"{username}@cafor.ci",
        is_staff=False,
        is_superuser=False
    )

    Employee.objects.create(
        user=user,
        first_name=agent['prenom'],
        last_name=agent['nom'],
        email=f"{username}@cafor.ci",
        department=cafor,
        direction=agent['service'],
        position='Chauffeur',
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
