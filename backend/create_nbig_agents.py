"""
Script pour créer les 35 agents NBIG SECURITE dans la base de données.
Exécuter avec: python manage.py shell < create_nbig_agents.py
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empmanager.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import Department, Employee

# Trouver ou créer l'entreprise NBIG SECURITE
dept, created = Department.objects.get_or_create(
    name='NBIG SECURITE',
    defaults={'description': 'Gardiennage - Sécurité Electronique - Sécurité Incendie'}
)
print(f"Entreprise NBIG SECURITE: {'créée' if created else 'existante'} (ID: {dept.id})")

# Liste des 35 agents NBIG
agents = [
    {'last_name': 'ATTA', 'first_name': 'Vianney Djabia', 'direction': 'DGIR ABIDJAN'},
    {'last_name': 'BEGBIN', 'first_name': 'Registre', 'direction': 'SDRH'},
    {'last_name': 'BOMISSO', 'first_name': 'Bale Aurel', 'direction': 'D.P.E ABIDJAN'},
    {'last_name': 'KOUADIO', 'first_name': 'Yao D\'Assises', 'direction': 'D.P.E ABIDJAN SUPERVISEUR'},
    {'last_name': 'KOUASSI', 'first_name': 'Koffi Jules', 'direction': 'DD ABIDJAN'},
    {'last_name': 'LOUA', 'first_name': 'Sopoude Barthelemy', 'direction': 'D.P.E ABIDJAN'},
    {'last_name': 'MODIBO', 'first_name': 'Guira', 'direction': 'DD ABIDJAN'},
    {'last_name': 'OSSORON', 'first_name': 'Nicaise', 'direction': 'D.P.E ABIDJAN'},
    {'last_name': 'ABODJO', 'first_name': 'Charles F', 'direction': 'DR YAKRO'},
    {'last_name': 'AKA', 'first_name': 'Romaric Armand', 'direction': 'DR DAOUKRO'},
    {'last_name': 'BAH', 'first_name': 'Bruno', 'direction': 'DR ABOISSO'},
    {'last_name': 'AKPOUE', 'first_name': 'Kouame Hyacinthe', 'direction': 'DD M\'BAHIAKRO'},
    {'last_name': 'COULIBALY', 'first_name': 'Kassim', 'direction': 'DR AGBOVILLE'},
    {'last_name': 'DIBY', 'first_name': 'Sranhoulou Paul', 'direction': 'DD DABOU'},
    {'last_name': 'GALE', 'first_name': 'Kelly Serge Pacome', 'direction': 'DTI ALEPE'},
    {'last_name': 'GBELI', 'first_name': 'Yoro Alfred', 'direction': 'DR MAN'},
    {'last_name': 'GBOTO', 'first_name': 'Sylvain', 'direction': 'DD GRD LAHOU'},
    {'last_name': 'GLAN', 'first_name': 'Adolphe', 'direction': 'DR DALOA'},
    {'last_name': 'DJOUBE', 'first_name': 'Jean Francois', 'direction': 'DR DIMBOKRO'},
    {'last_name': 'AHUA', 'first_name': 'Emile Miezan', 'direction': 'DT KATIOLA'},
    {'last_name': 'KOFFI', 'first_name': 'Kouame Leon', 'direction': 'DD DALOA'},
    {'last_name': 'KOHO', 'first_name': 'Zakpa Etienne', 'direction': 'DD SINFRA'},
    {'last_name': 'KONAN', 'first_name': 'Kouassi Joseph', 'direction': 'DD BOUAFLE'},
    {'last_name': 'KONE', 'first_name': 'Daouda', 'direction': 'DTH DALOA'},
    {'last_name': 'KONE', 'first_name': 'Issa', 'direction': 'DD AGNIBILEKRO'},
    {'last_name': 'KORAHI', 'first_name': 'Ibo Bernard', 'direction': 'DD DIVO'},
    {'last_name': 'KPAN', 'first_name': 'Ounguia Bejamin', 'direction': 'DR GUIGLO'},
    {'last_name': 'KPAWO', 'first_name': 'Troh Frederic', 'direction': 'DD TIASSALE'},
    {'last_name': 'MAHAN', 'first_name': 'Etienne', 'direction': 'DD JACQUEVILLE'},
    {'last_name': 'MANIGA', 'first_name': 'Sahi', 'direction': 'DR TOUBA'},
    {'last_name': 'NAKPALO', 'first_name': 'Fissini Yeo', 'direction': 'DD ISSIA'},
    {'last_name': 'OUATTARA', 'first_name': 'Djibokori', 'direction': 'DR BOUNA'},
    {'last_name': 'SOKRO', 'first_name': 'Nguessan Jean', 'direction': 'DD GRD BASSAM'},
    {'last_name': 'YOUAN', 'first_name': 'Bi Voli', 'direction': 'DR AGBOVILLE'},
    {'last_name': 'ZADI', 'first_name': 'Guy Daniel', 'direction': 'DD ZUENOULA'},
]


def generate_username(first_name, last_name, existing_usernames):
    """Génère un nom d'utilisateur unique: prenom.nom"""
    prenom = first_name.split()[0].lower()
    nom = last_name.lower()
    # Supprimer les caractères spéciaux
    for char in "'-":
        prenom = prenom.replace(char, '')
        nom = nom.replace(char, '')
    username = f"{prenom}.{nom}"
    # Si le username existe déjà, ajouter un numéro
    if username in existing_usernames:
        i = 2
        while f"{username}{i}" in existing_usernames:
            i += 1
        username = f"{username}{i}"
    return username


def generate_password(last_name, index):
    """Génère un mot de passe unique: Nbig@Nom+numéro"""
    nom = last_name.capitalize()[:4]
    return f"Nbig@{nom}{index:02d}"


# Collecter les usernames existants
existing_usernames = set(User.objects.values_list('username', flat=True))

# Résultats pour affichage
results = []
created_count = 0
skipped_count = 0

print("\n" + "=" * 80)
print("CRÉATION DES COMPTES AGENTS NBIG SECURITE")
print("=" * 80)

for i, agent in enumerate(agents, 1):
    username = generate_username(agent['first_name'], agent['last_name'], existing_usernames)
    password = generate_password(agent['last_name'], i)

    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(username=username).exists():
        print(f"  [SKIP] {agent['last_name']} {agent['first_name']} - utilisateur '{username}' existe déjà")
        skipped_count += 1
        continue

    # Créer l'utilisateur Django (rôle employé = is_staff=False, is_superuser=False)
    user = User.objects.create_user(
        username=username,
        password=password,
        first_name=agent['first_name'],
        last_name=agent['last_name'],
        email=f"{username}@nbig-securite.ci",
        is_staff=False,
        is_superuser=False
    )

    # Créer le profil employé
    employee = Employee.objects.create(
        user=user,
        first_name=agent['first_name'],
        last_name=agent['last_name'],
        email=f"{username}@nbig-securite.ci",
        department=dept,
        direction=agent['direction'],
        position='Vigile',
        hire_date='2025-12-01',
        status='active',
        salary=0,
    )

    existing_usernames.add(username)
    created_count += 1

    results.append({
        'num': i,
        'nom_complet': f"{agent['last_name']} {agent['first_name']}",
        'username': username,
        'password': password,
        'direction': agent['direction'],
    })

    print(f"  [OK] {i:02d}. {agent['last_name']} {agent['first_name']} -> {username}")

print(f"\n{'=' * 80}")
print(f"RÉSULTAT: {created_count} comptes créés, {skipped_count} ignorés")
print(f"{'=' * 80}")

# Afficher le tableau des identifiants
print(f"\n{'=' * 90}")
print(f"{'N°':>3} | {'NOM ET PRÉNOMS':<30} | {'IDENTIFIANT':<22} | {'MOT DE PASSE':<15} | {'AFFECTATION':<20}")
print(f"{'-' * 90}")
for r in results:
    print(f"{r['num']:>3} | {r['nom_complet']:<30} | {r['username']:<22} | {r['password']:<15} | {r['direction']:<20}")
print(f"{'=' * 90}")
print("\nTerminé !")
