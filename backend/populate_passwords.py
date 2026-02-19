"""
Script pour remplir la table PasswordRecord avec les mots de passe connus.
Exécuter avec: python manage.py shell < populate_passwords.py
Ou directement: venv\Scripts\python.exe -c "exec(open('populate_passwords.py', encoding='utf-8').read())"
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'empmanager.settings')
django.setup()

from django.contrib.auth.models import User
from api.models import PasswordRecord
from api.encryption import encrypt_password

# Liste des 35 agents NBIG avec leurs mots de passe générés
nbig_agents = [
    {'username': 'vianney.atta', 'password': 'Nbig@Atta01'},
    {'username': 'registre.begbin', 'password': 'Nbig@Begb02'},
    {'username': 'bale.bomisso', 'password': 'Nbig@Bomi03'},
    {'username': 'yao.kouadio', 'password': 'Nbig@Koua04'},
    {'username': 'koffi.kouassi', 'password': 'Nbig@Koua05'},
    {'username': 'sopoude.loua', 'password': 'Nbig@Loua06'},
    {'username': 'guira.modibo', 'password': 'Nbig@Modi07'},
    {'username': 'nicaise.ossoron', 'password': 'Nbig@Osso08'},
    {'username': 'charles.abodjo', 'password': 'Nbig@Abod09'},
    {'username': 'romaric.aka', 'password': 'Nbig@Aka10'},
    {'username': 'bruno.bah', 'password': 'Nbig@Bah11'},
    {'username': 'kouame.akpoue', 'password': 'Nbig@Akpo12'},
    {'username': 'kassim.coulibaly', 'password': 'Nbig@Coul13'},
    {'username': 'sranhoulou.diby', 'password': 'Nbig@Diby14'},
    {'username': 'kelly.gale', 'password': 'Nbig@Gale15'},
    {'username': 'yoro.gbeli', 'password': 'Nbig@Gbel16'},
    {'username': 'sylvain.gboto', 'password': 'Nbig@Gbot17'},
    {'username': 'adolphe.glan', 'password': 'Nbig@Glan18'},
    {'username': 'jean.djoube', 'password': 'Nbig@Djou19'},
    {'username': 'emile.ahua', 'password': 'Nbig@Ahua20'},
    {'username': 'kouame.koffi', 'password': 'Nbig@Koff21'},
    {'username': 'zakpa.koho', 'password': 'Nbig@Koho22'},
    {'username': 'kouassi.konan', 'password': 'Nbig@Kona23'},
    {'username': 'daouda.kone', 'password': 'Nbig@Kone24'},
    {'username': 'issa.kone', 'password': 'Nbig@Kone25'},
    {'username': 'ibo.korahi', 'password': 'Nbig@Kora26'},
    {'username': 'ounguia.kpan', 'password': 'Nbig@Kpan27'},
    {'username': 'troh.kpawo', 'password': 'Nbig@Kpaw28'},
    {'username': 'etienne.mahan', 'password': 'Nbig@Maha29'},
    {'username': 'sahi.maniga', 'password': 'Nbig@Mani30'},
    {'username': 'fissini.nakpalo', 'password': 'Nbig@Nakp31'},
    {'username': 'djibokori.ouattara', 'password': 'Nbig@Ouat32'},
    {'username': 'nguessan.sokro', 'password': 'Nbig@Sokr33'},
    {'username': 'bi.youan', 'password': 'Nbig@Youa34'},
    {'username': 'guy.zadi', 'password': 'Nbig@Zadi35'},
]

print("=" * 70)
print("REMPLISSAGE DE LA TABLE DES MOTS DE PASSE")
print("=" * 70)

created_count = 0
skipped_count = 0
not_found = 0

# 1. Enregistrer les mots de passe des agents NBIG
for agent in nbig_agents:
    try:
        user = User.objects.get(username=agent['username'])
        role = 'employee'
        record, created = PasswordRecord.objects.update_or_create(
            user=user,
            defaults={
                'password_encrypted': encrypt_password(agent['password']),
                'role': role,
            }
        )
        if created:
            created_count += 1
            print(f"  [OK] {user.get_full_name()} ({agent['username']}) -> {agent['password']}")
        else:
            skipped_count += 1
            print(f"  [MAJ] {user.get_full_name()} ({agent['username']}) -> mot de passe mis a jour")
    except User.DoesNotExist:
        not_found += 1
        print(f"  [ERREUR] Utilisateur '{agent['username']}' non trouve")

# 2. Enregistrer tous les autres utilisateurs dont le mot de passe n'est pas dans la table
print(f"\n--- Verification des autres utilisateurs ---")
other_users = User.objects.exclude(
    username__in=[a['username'] for a in nbig_agents]
)
for user in other_users:
    if not PasswordRecord.objects.filter(user=user).exists():
        # Determiner le role
        if user.is_superuser:
            role = 'admin'
        elif user.is_staff:
            role = 'manager'
        else:
            role = 'employee'

        PasswordRecord.objects.create(
            user=user,
            password_encrypted=encrypt_password('(mot de passe inconnu)'),
            role=role,
        )
        created_count += 1
        print(f"  [AJOUT] {user.get_full_name() or user.username} ({user.username}) - role: {role} - mot de passe inconnu")

print(f"\n{'=' * 70}")
print(f"RESULTAT: {created_count} enregistrements crees, {skipped_count} mis a jour, {not_found} non trouves")
print(f"{'=' * 70}")
print("Termine !")
