"""
Tests unitaires — API Gestion du Personnel Contractuel DAF-MEER
Lancer avec : python manage.py test api
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import date, timedelta, time

from .models import (
    Department, Direction, Employee, Leave,
    Attendance, PasswordRecord, ManagerProfile, CompanyProfile
)


# ===========================
# Helpers de création
# ===========================

def make_admin(username='admin', password='admin123'):
    return User.objects.create_superuser(
        username=username, password=password, email=f'{username}@test.com'
    )


def make_manager(username='manager', password='manager123'):
    return User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com', is_staff=True
    )


def make_regular_user(username='emp', password='emp123'):
    return User.objects.create_user(
        username=username, password=password, email=f'{username}@test.com'
    )


def make_entreprise_user(username, dept, password='emp123'):
    """Crée un utilisateur entreprise : is_staff=True + CompanyProfile (requis par les ViewSets)"""
    user = User.objects.create_user(
        username=username, password=password,
        email=f'{username}@test.com', is_staff=True
    )
    CompanyProfile.objects.create(user=user, department=dept)
    return user


def make_department(name='AZING'):
    return Department.objects.create(name=name, manager='Responsable', description='Entreprise test')


def make_employee(dept, user=None, first_name='Jean', last_name='Dupont', direction=None):
    """Crée un employé — email et matricule basés sur prénom+nom (uniques par test)"""
    tag = f'{first_name.lower()}{last_name.lower()}'
    return Employee.objects.create(
        first_name=first_name,
        last_name=last_name,
        email=f'{tag}@test.com',
        phone='0102030405',
        department=dept,
        direction=direction,
        position='Agent',
        hire_date=date(2020, 1, 15),
        salary=150000,
        matricule=f'MAT-{tag[:6].upper()}',
        cnps=f'CNPS{tag[:6].upper()}',
        address='Abidjan',
        user=user,
    )


# ===========================
# 1. Tests des Modèles
# ===========================

class TestEmployeeModel(TestCase):
    """Propriétés calculées du modèle Employee"""

    def setUp(self):
        self.dept = make_department()
        self.emp = make_employee(self.dept)

    def test_full_name(self):
        self.assertEqual(self.emp.full_name, 'Jean Dupont')

    def test_leave_balance_initial_is_max(self):
        # Aucun congé approuvé → solde plein (30 jours)
        self.assertEqual(self.emp.leave_balance, 30)

    def test_leave_balance_decreases_after_approved_leave(self):
        Leave.objects.create(
            employee=self.emp,
            leave_type='paid',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),  # 5 jours
            reason='Vacances',
            status='approved',
        )
        self.assertEqual(self.emp.leave_balance, 25)

    def test_leave_balance_unaffected_by_pending_leave(self):
        Leave.objects.create(
            employee=self.emp,
            leave_type='paid',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
            reason='Vacances',
            status='pending',
        )
        self.assertEqual(self.emp.leave_balance, 30)

    def test_leave_balance_unaffected_by_rejected_leave(self):
        Leave.objects.create(
            employee=self.emp,
            leave_type='paid',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
            reason='Refusé',
            status='rejected',
        )
        self.assertEqual(self.emp.leave_balance, 30)

    def test_sick_leave_does_not_reduce_paid_balance(self):
        """Un congé maladie approuvé ne doit pas réduire le solde de congés payés"""
        Leave.objects.create(
            employee=self.emp,
            leave_type='sick',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=9),  # 10 jours de maladie
            reason='Grippe',
            status='approved',
        )
        self.assertEqual(self.emp.leave_balance, 30)  # inchangé

    def test_unpaid_leave_does_not_reduce_paid_balance(self):
        Leave.objects.create(
            employee=self.emp,
            leave_type='unpaid',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=4),
            reason='Personnel',
            status='approved',
        )
        self.assertEqual(self.emp.leave_balance, 30)  # inchangé


class TestLeaveModel(TestCase):
    """Propriétés calculées du modèle Leave"""

    def setUp(self):
        self.dept = make_department()
        self.emp = make_employee(self.dept)

    def test_days_count_multi_day(self):
        leave = Leave.objects.create(
            employee=self.emp,
            leave_type='paid',
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 14),
            reason='Repos',
        )
        self.assertEqual(leave.days_count, 5)

    def test_days_count_single_day(self):
        leave = Leave.objects.create(
            employee=self.emp,
            leave_type='sick',
            start_date=date(2026, 2, 10),
            end_date=date(2026, 2, 10),
            reason='Maladie',
        )
        self.assertEqual(leave.days_count, 1)


class TestAttendanceModel(TestCase):
    """Propriétés calculées du modèle Attendance"""

    def setUp(self):
        self.dept = make_department()
        self.emp = make_employee(self.dept)

    def test_hours_worked_full_day(self):
        att = Attendance.objects.create(
            employee=self.emp,
            date=date.today(),
            check_in=time(8, 0),
            check_out=time(17, 0),
            status='present',
        )
        self.assertEqual(att.hours_worked, 9.0)

    def test_hours_worked_without_checkout_is_zero(self):
        att = Attendance.objects.create(
            employee=self.emp,
            date=date.today(),
            check_in=time(8, 0),
            status='present',
        )
        self.assertEqual(att.hours_worked, 0)


# ===========================
# 2. Tests d'Authentification
# ===========================

class TestLoginAPI(APITestCase):
    """Login → détermine le rôle automatiquement"""

    url = '/api/auth/login/'

    def setUp(self):
        make_admin()
        make_manager()
        make_regular_user()
        dept = make_department()
        make_entreprise_user('ent_user', dept)

    def test_admin_role_detected(self):
        resp = self.client.post(self.url, {'username': 'admin', 'password': 'admin123'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['user']['role'], 'admin')

    def test_manager_role_detected(self):
        resp = self.client.post(self.url, {'username': 'manager', 'password': 'manager123'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['user']['role'], 'manager')

    def test_employee_role_detected(self):
        resp = self.client.post(self.url, {'username': 'emp', 'password': 'emp123'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['user']['role'], 'employee')

    def test_entreprise_role_detected(self):
        resp = self.client.post(self.url, {'username': 'ent_user', 'password': 'emp123'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['user']['role'], 'entreprise')

    def test_invalid_credentials_returns_401(self):
        resp = self.client.post(self.url, {'username': 'admin', 'password': 'mauvais'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_returns_jwt_access_and_refresh(self):
        resp = self.client.post(self.url, {'username': 'admin', 'password': 'admin123'})
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_unauthenticated_access_to_protected_endpoint_returns_401(self):
        resp = self.client.get('/api/employees/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ===========================
# 3. Tests de Contrôle d'Accès
# ===========================

class TestPasswordRecordAccess(APITestCase):
    """Seuls les admins (is_staff) peuvent accéder aux mots de passe"""

    url = '/api/passwords/'

    def setUp(self):
        self.admin = make_admin()
        self.manager = make_manager()
        self.emp_user = make_regular_user()

    def test_admin_can_list_passwords(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_manager_can_list_passwords(self):
        # is_staff=True donc IsAdminUser autorise
        self.client.force_authenticate(user=self.manager)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_employee_gets_403_on_passwords(self):
        self.client.force_authenticate(user=self.emp_user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_gets_401_on_passwords(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class TestEmployeeAccessByRole(APITestCase):
    """Chaque rôle ne voit que les employés autorisés"""

    url = '/api/employees/'

    def setUp(self):
        self.dept1 = make_department('AZING')
        self.dept2 = make_department('CAFOR')

        # Admin
        self.admin = make_admin()

        # Entreprise liée à dept1
        self.ent_user = make_entreprise_user('ent', self.dept1)

        # Manager lié à la direction "DIR-A"
        self.mgr_user = make_manager('mgr')
        direction = Direction.objects.create(name='DIR-A')
        profile = ManagerProfile.objects.create(user=self.mgr_user)
        profile.directions.add(direction)

        # Employés
        self.alice = make_employee(self.dept1, first_name='Alice', last_name='A', direction='DIR-A')
        self.bob = make_employee(self.dept1, first_name='Bob', last_name='B')    # dept1, sans direction
        self.carol = make_employee(self.dept2, first_name='Carol', last_name='C')  # dept2

        # Utilisateur employé lié à Alice
        self.alice_user = make_regular_user('alice_user')
        self.alice.user = self.alice_user
        self.alice.save()

    def _names(self, resp):
        return [e['first_name'] for e in resp.data]

    def test_admin_sees_all_employees(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 3)

    def test_entreprise_sees_only_own_dept(self):
        self.client.force_authenticate(user=self.ent_user)
        resp = self.client.get(self.url)
        names = self._names(resp)
        self.assertIn('Alice', names)
        self.assertIn('Bob', names)
        self.assertNotIn('Carol', names)

    def test_manager_sees_only_own_direction(self):
        self.client.force_authenticate(user=self.mgr_user)
        resp = self.client.get(self.url)
        names = self._names(resp)
        self.assertIn('Alice', names)
        self.assertNotIn('Bob', names)   # même dept mais autre direction
        self.assertNotIn('Carol', names)  # autre dept

    def test_employee_sees_only_self(self):
        self.client.force_authenticate(user=self.alice_user)
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.data), 1)
        self.assertEqual(resp.data[0]['first_name'], 'Alice')


# ===========================
# 4. Tests du Workflow Congés
# ===========================

class TestLeaveWorkflow(APITestCase):
    """Approbation en deux étapes : Manager → Entreprise (ou Admin direct)"""

    def setUp(self):
        self.dept = make_department()

        # Admin
        self.admin = make_admin()

        # Manager avec direction
        self.mgr_user = make_manager('mgr_leave')
        direction = Direction.objects.create(name='DIR-TEST')
        mgr_profile = ManagerProfile.objects.create(user=self.mgr_user)
        mgr_profile.directions.add(direction)

        # Entreprise
        self.ent_user = make_entreprise_user('ent_leave', self.dept)

        # Employé dans la direction
        self.emp = make_employee(
            self.dept, direction='DIR-TEST', first_name='Paul', last_name='Martin'
        )

        # Congé en attente
        self.leave = Leave.objects.create(
            employee=self.emp,
            leave_type='paid',
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            reason='Repos familial',
            status='pending',
        )

    def _approve(self, user):
        self.client.force_authenticate(user=user)
        return self.client.post(f'/api/leaves/{self.leave.id}/approve/')

    def _reject(self, user):
        self.client.force_authenticate(user=user)
        return self.client.post(f'/api/leaves/{self.leave.id}/reject/')

    def test_manager_valide_congé_pending(self):
        resp = self._approve(self.mgr_user)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'manager_approved')
        self.assertEqual(self.leave.manager_approved_by, self.mgr_user)

    def test_entreprise_ne_peut_pas_approuver_un_congé_pending(self):
        # L'entreprise doit attendre la validation du manager
        resp = self._approve(self.ent_user)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'pending')  # inchangé

    def test_entreprise_approuve_après_validation_manager(self):
        self.leave.status = 'manager_approved'
        self.leave.manager_approved_by = self.mgr_user
        self.leave.save()

        resp = self._approve(self.ent_user)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'approved')
        self.assertEqual(self.leave.approved_by, self.ent_user)

    def test_admin_approuve_directement_sans_manager(self):
        resp = self._approve(self.admin)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'approved')

    def test_manager_rejette_congé_pending(self):
        resp = self._reject(self.mgr_user)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'rejected')

    def test_impossible_de_rejeter_un_congé_déjà_approuvé(self):
        self.leave.status = 'approved'
        self.leave.save()

        resp = self._reject(self.admin)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'approved')  # inchangé

    def test_impossible_de_rejeter_un_congé_déjà_rejeté(self):
        self.leave.status = 'rejected'
        self.leave.save()

        resp = self._reject(self.admin)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_employé_ne_peut_pas_rejeter_son_propre_congé(self):
        """Un agent ne peut pas rejeter lui-même sa demande"""
        emp_user = make_regular_user('emp_own')
        self.emp.user = emp_user
        self.emp.save()

        self.client.force_authenticate(user=emp_user)
        resp = self.client.post(f'/api/leaves/{self.leave.id}/reject/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.status, 'pending')  # inchangé

    def test_suppression_congé_pending_autorisée(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.delete(f'/api/leaves/{self.leave.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)

    def test_suppression_congé_approuvé_interdite(self):
        self.leave.status = 'approved'
        self.leave.save()

        self.client.force_authenticate(user=self.admin)
        resp = self.client.delete(f'/api/leaves/{self.leave.id}/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Leave.objects.filter(id=self.leave.id).exists())


# ===========================
# 5. Tests des Rapports Excel
# ===========================

class TestExcelReports(APITestCase):
    """Les rapports retournent un fichier .xlsx valide"""

    XLSX_CONTENT_TYPE = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

    def setUp(self):
        self.admin = make_admin()
        dept = make_department()
        emp = make_employee(dept, first_name='Test', last_name='Rapport')
        Leave.objects.create(
            employee=emp,
            leave_type='paid',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            reason='Test',
            status='approved',
        )
        Attendance.objects.create(
            employee=emp,
            date=date.today(),
            check_in=time(8, 0),
            check_out=time(17, 0),
            status='present',
        )

    def _get(self, url):
        self.client.force_authenticate(user=self.admin)
        return self.client.get(url)

    def test_rapport_presences(self):
        resp = self._get('/api/reports/attendance/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp['Content-Type'], self.XLSX_CONTENT_TYPE)
        self.assertIn('Rapport_Presences_', resp['Content-Disposition'])

    def test_rapport_conges(self):
        resp = self._get('/api/reports/leaves/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp['Content-Type'], self.XLSX_CONTENT_TYPE)
        self.assertIn('Rapport_Conges_', resp['Content-Disposition'])

    def test_rapport_par_entreprise(self):
        resp = self._get('/api/reports/departments/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp['Content-Type'], self.XLSX_CONTENT_TYPE)
        self.assertIn('Rapport_Entreprises_', resp['Content-Disposition'])

    def test_rapport_rh_complet(self):
        resp = self._get('/api/reports/complete/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp['Content-Type'], self.XLSX_CONTENT_TYPE)
        self.assertIn('Rapport_RH_Complet_', resp['Content-Disposition'])

    def test_non_authentifié_ne_peut_pas_télécharger_rapport(self):
        resp = self.client.get('/api/reports/complete/')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ===========================
# 6. Tests des Sérialiseurs
# ===========================

class TestLeaveSerializerValidation(TestCase):
    """Validation des dates et du solde dans LeaveSerializer"""

    def setUp(self):
        self.dept = make_department()
        self.emp = make_employee(self.dept)

    def test_date_fin_avant_date_début_est_invalide(self):
        from .serializers import LeaveSerializer
        data = {
            'employee': self.emp.id,
            'leave_type': 'sick',
            'start_date': '2026-03-10',
            'end_date': '2026-03-05',
            'reason': 'Test',
        }
        serializer = LeaveSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)

    def test_dates_valides_sont_acceptées(self):
        from .serializers import LeaveSerializer
        data = {
            'employee': self.emp.id,
            'leave_type': 'sick',
            'start_date': '2026-03-10',
            'end_date': '2026-03-12',
            'reason': 'Maladie',
        }
        serializer = LeaveSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)

    def test_congé_payé_au_delà_du_solde_est_invalide(self):
        from .serializers import LeaveSerializer
        # 35 jours demandés > 30 jours de solde
        data = {
            'employee': self.emp.id,
            'leave_type': 'paid',
            'start_date': str(date.today() + timedelta(days=1)),
            'end_date': str(date.today() + timedelta(days=35)),
            'reason': 'Trop long',
        }
        serializer = LeaveSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_date', serializer.errors)


class TestAttendanceSerializerValidation(TestCase):
    """Validation des heures dans AttendanceSerializer"""

    def setUp(self):
        self.dept = make_department()
        self.emp = make_employee(self.dept)

    def test_checkout_avant_checkin_est_invalide(self):
        from .serializers import AttendanceSerializer
        data = {
            'employee': self.emp.id,
            'date': str(date.today()),
            'check_in': '10:00',
            'check_out': '08:00',
            'status': 'present',
        }
        serializer = AttendanceSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('check_out', serializer.errors)

    def test_heures_valides_sont_acceptées(self):
        from .serializers import AttendanceSerializer
        data = {
            'employee': self.emp.id,
            'date': str(date.today()),
            'check_in': '08:00',
            'check_out': '17:00',
            'status': 'present',
        }
        serializer = AttendanceSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)


# ===========================
# 7. Tests du Chiffrement
# ===========================

class TestEncryption(TestCase):
    """encrypt_password / decrypt_password / PasswordRecord.set_password / get_password"""

    def test_encrypt_returns_non_empty_string(self):
        from .encryption import encrypt_password
        result = encrypt_password('monMotDePasse')
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    def test_encrypted_value_differs_from_plain(self):
        from .encryption import encrypt_password
        plain = 'secret123'
        self.assertNotEqual(encrypt_password(plain), plain)

    def test_decrypt_recovers_original(self):
        from .encryption import encrypt_password, decrypt_password
        plain = 'Abidjan@2026!'
        self.assertEqual(decrypt_password(encrypt_password(plain)), plain)

    def test_decrypt_invalid_token_returns_fallback(self):
        from .encryption import decrypt_password
        self.assertEqual(decrypt_password('pasUneValeurFernet'), '(indéchiffrable)')

    def test_decrypt_empty_string_returns_fallback(self):
        from .encryption import decrypt_password
        self.assertEqual(decrypt_password(''), '(indéchiffrable)')

    def test_two_encryptions_of_same_value_differ(self):
        """Fernet génère un IV aléatoire → deux chiffrements ≠ même résultat"""
        from .encryption import encrypt_password
        plain = 'identique'
        self.assertNotEqual(encrypt_password(plain), encrypt_password(plain))

    def test_password_record_set_and_get_password(self):
        """PasswordRecord.set_password + get_password font un aller-retour correct"""
        dept = make_department('ENC-DEPT')
        emp_user = make_regular_user('enc_user')
        record = PasswordRecord(user=emp_user, role='employee')
        record.set_password('MonMotDePasse99')
        # L'attribut interne est chiffré
        self.assertNotEqual(record.password_encrypted, 'MonMotDePasse99')
        # get_password redonne le clair
        self.assertEqual(record.get_password(), 'MonMotDePasse99')

    def test_password_record_stored_encrypted_in_db(self):
        """Le champ en base ne contient jamais le mot de passe en clair"""
        emp_user = make_regular_user('db_enc_user')
        record = PasswordRecord(user=emp_user, role='employee')
        record.set_password('TopSecret!')
        record.save()

        fresh = PasswordRecord.objects.get(user=emp_user)
        self.assertNotEqual(fresh.password_encrypted, 'TopSecret!')
        self.assertEqual(fresh.get_password(), 'TopSecret!')

    def test_password_record_api_exposes_decrypted_value(self):
        """L'API /passwords/ retourne le mot de passe déchiffré (champ password_plain)"""
        from rest_framework.test import APIClient
        admin = make_admin('admin_enc')
        emp_user = make_regular_user('api_enc_user')
        record = PasswordRecord(user=emp_user, role='employee')
        record.set_password('ApiSecret42')
        record.save()

        client = APIClient()
        client.force_authenticate(user=admin)
        resp = client.get('/api/passwords/')
        self.assertEqual(resp.status_code, 200)
        passwords = [r['password_plain'] for r in resp.data]
        self.assertIn('ApiSecret42', passwords)


# ===========================
# 8. Tests de get_user_context()
# ===========================

class TestGetUserContext(TestCase):
    """get_user_context() identifie correctement le rôle de chaque utilisateur"""

    def setUp(self):
        from .views import get_user_context
        self.get_user_context = get_user_context
        self.dept = make_department('CTX-DEPT')

    def test_superuser_retourne_role_admin(self):
        admin = make_admin('ctx_admin')
        ctx = self.get_user_context(admin)
        self.assertEqual(ctx['role'], 'admin')
        self.assertNotIn('department', ctx)
        self.assertNotIn('directions', ctx)

    def test_user_avec_company_profile_retourne_role_entreprise(self):
        ent = make_entreprise_user('ctx_ent', self.dept)
        ctx = self.get_user_context(ent)
        self.assertEqual(ctx['role'], 'entreprise')
        self.assertEqual(ctx['department'], self.dept)

    def test_is_staff_avec_manager_profile_retourne_role_manager(self):
        mgr = make_manager('ctx_mgr')
        direction = Direction.objects.create(name='CTX-DIR')
        profile = ManagerProfile.objects.create(user=mgr)
        profile.directions.add(direction)

        ctx = self.get_user_context(mgr)
        self.assertEqual(ctx['role'], 'manager')
        self.assertIn('CTX-DIR', ctx['directions'])

    def test_manager_sans_direction_retourne_liste_vide(self):
        mgr = make_manager('ctx_mgr_no_dir')
        ManagerProfile.objects.create(user=mgr)
        ctx = self.get_user_context(mgr)
        self.assertEqual(ctx['role'], 'manager')
        self.assertEqual(ctx['directions'], [])

    def test_utilisateur_normal_retourne_role_employee(self):
        emp_user = make_regular_user('ctx_emp')
        ctx = self.get_user_context(emp_user)
        self.assertEqual(ctx['role'], 'employee')

    def test_superuser_avec_company_profile_reste_admin(self):
        """Un superuser a toujours le rôle admin, même s'il a un CompanyProfile"""
        admin = make_admin('ctx_super_ent')
        CompanyProfile.objects.create(user=admin, department=self.dept)
        ctx = self.get_user_context(admin)
        self.assertEqual(ctx['role'], 'admin')


# ===========================
# 9. Tests d'isolation des Congés par rôle
# ===========================

class TestLeaveAccessByRole(APITestCase):
    """Chaque rôle ne voit que les congés de ses employés"""

    url = '/api/leaves/'

    def setUp(self):
        self.dept1 = make_department('LEAVE-DEPT1')
        self.dept2 = make_department('LEAVE-DEPT2')

        self.admin = make_admin('leave_admin')
        self.ent_user = make_entreprise_user('leave_ent', self.dept1)

        direction = Direction.objects.create(name='LEAVE-DIR')
        self.mgr_user = make_manager('leave_mgr')
        mgr_profile = ManagerProfile.objects.create(user=self.mgr_user)
        mgr_profile.directions.add(direction)

        # Employés
        self.emp1 = make_employee(self.dept1, direction='LEAVE-DIR',
                                  first_name='L1', last_name='Test')
        self.emp2 = make_employee(self.dept1, first_name='L2', last_name='Test')
        self.emp3 = make_employee(self.dept2, first_name='L3', last_name='Test')

        # Congés
        def _leave(emp, days=1):
            return Leave.objects.create(
                employee=emp,
                leave_type='sick',
                start_date=date.today(),
                end_date=date.today() + timedelta(days=days - 1),
                reason='Test',
            )

        self.leave1 = _leave(self.emp1)   # dept1, direction LEAVE-DIR
        self.leave2 = _leave(self.emp2)   # dept1, sans direction
        self.leave3 = _leave(self.emp3)   # dept2

    def _ids(self, resp):
        return {r['id'] for r in resp.data}

    def test_admin_voit_tous_les_congés(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.leave1.id, self._ids(resp))
        self.assertIn(self.leave2.id, self._ids(resp))
        self.assertIn(self.leave3.id, self._ids(resp))

    def test_entreprise_voit_seulement_dept1(self):
        self.client.force_authenticate(user=self.ent_user)
        resp = self.client.get(self.url)
        ids = self._ids(resp)
        self.assertIn(self.leave1.id, ids)
        self.assertIn(self.leave2.id, ids)
        self.assertNotIn(self.leave3.id, ids)

    def test_manager_voit_seulement_sa_direction(self):
        self.client.force_authenticate(user=self.mgr_user)
        resp = self.client.get(self.url)
        ids = self._ids(resp)
        self.assertIn(self.leave1.id, ids)
        self.assertNotIn(self.leave2.id, ids)
        self.assertNotIn(self.leave3.id, ids)

    def test_employé_voit_seulement_ses_congés(self):
        emp_user = make_regular_user('leave_emp_user')
        self.emp1.user = emp_user
        self.emp1.save()

        self.client.force_authenticate(user=emp_user)
        resp = self.client.get(self.url)
        ids = self._ids(resp)
        self.assertIn(self.leave1.id, ids)
        self.assertNotIn(self.leave2.id, ids)
        self.assertNotIn(self.leave3.id, ids)


# ===========================
# 10. Tests d'isolation des Présences par rôle
# ===========================

class TestAttendanceAccessByRole(APITestCase):
    """Chaque rôle ne voit que les présences de ses employés"""

    url = '/api/attendances/'

    def setUp(self):
        self.dept1 = make_department('ATT-DEPT1')
        self.dept2 = make_department('ATT-DEPT2')

        self.admin = make_admin('att_admin')
        self.ent_user = make_entreprise_user('att_ent', self.dept1)

        direction = Direction.objects.create(name='ATT-DIR')
        self.mgr_user = make_manager('att_mgr')
        mgr_profile = ManagerProfile.objects.create(user=self.mgr_user)
        mgr_profile.directions.add(direction)

        self.emp1 = make_employee(self.dept1, direction='ATT-DIR',
                                  first_name='A1', last_name='Test')
        self.emp2 = make_employee(self.dept1, first_name='A2', last_name='Test')
        self.emp3 = make_employee(self.dept2, first_name='A3', last_name='Test')

        def _att(emp, day_offset=0):
            return Attendance.objects.create(
                employee=emp,
                date=date.today() - timedelta(days=day_offset),
                check_in=time(8, 0),
                status='present',
            )

        self.att1 = _att(self.emp1)
        self.att2 = _att(self.emp2, day_offset=1)
        self.att3 = _att(self.emp3, day_offset=2)

    def _ids(self, resp):
        return {r['id'] for r in resp.data}

    def test_admin_voit_toutes_les_présences(self):
        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        ids = self._ids(resp)
        self.assertIn(self.att1.id, ids)
        self.assertIn(self.att2.id, ids)
        self.assertIn(self.att3.id, ids)

    def test_entreprise_voit_seulement_dept1(self):
        self.client.force_authenticate(user=self.ent_user)
        resp = self.client.get(self.url)
        ids = self._ids(resp)
        self.assertIn(self.att1.id, ids)
        self.assertIn(self.att2.id, ids)
        self.assertNotIn(self.att3.id, ids)

    def test_manager_voit_seulement_sa_direction(self):
        self.client.force_authenticate(user=self.mgr_user)
        resp = self.client.get(self.url)
        ids = self._ids(resp)
        self.assertIn(self.att1.id, ids)
        self.assertNotIn(self.att2.id, ids)
        self.assertNotIn(self.att3.id, ids)

    def test_employé_voit_seulement_ses_présences(self):
        emp_user = make_regular_user('att_emp_user')
        self.emp1.user = emp_user
        self.emp1.save()

        self.client.force_authenticate(user=emp_user)
        resp = self.client.get(self.url)
        ids = self._ids(resp)
        self.assertIn(self.att1.id, ids)
        self.assertNotIn(self.att2.id, ids)
        self.assertNotIn(self.att3.id, ids)


# ===========================
# 11. Tests des Statistiques du Dashboard
# ===========================

class TestDashboardStats(APITestCase):
    """DashboardStatsView retourne des compteurs filtrés selon le rôle"""

    url = '/api/dashboard/stats/'

    def setUp(self):
        self.dept1 = make_department('STAT-DEPT1')
        self.dept2 = make_department('STAT-DEPT2')

        self.admin = make_admin('stat_admin')
        self.ent_user = make_entreprise_user('stat_ent', self.dept1)

        direction = Direction.objects.create(name='STAT-DIR')
        self.mgr_user = make_manager('stat_mgr')
        mgr_profile = ManagerProfile.objects.create(user=self.mgr_user)
        mgr_profile.directions.add(direction)

        # 2 employés dept1 (1 dans STAT-DIR), 1 employé dept2
        self.emp1 = make_employee(self.dept1, direction='STAT-DIR',
                                  first_name='S1', last_name='T')
        self.emp2 = make_employee(self.dept1, first_name='S2', last_name='T')
        self.emp3 = make_employee(self.dept2, first_name='S3', last_name='T')

        # Présences aujourd'hui
        Attendance.objects.create(employee=self.emp1, date=date.today(),
                                  status='present')
        Attendance.objects.create(employee=self.emp3, date=date.today(),
                                  status='present')

    def _stats(self, user):
        self.client.force_authenticate(user=user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        return resp.data

    def test_admin_voit_tous_les_employés(self):
        stats = self._stats(self.admin)
        self.assertEqual(stats['total_employees'], 3)

    def test_entreprise_voit_seulement_son_dept(self):
        stats = self._stats(self.ent_user)
        self.assertEqual(stats['total_employees'], 2)

    def test_manager_voit_seulement_sa_direction(self):
        stats = self._stats(self.mgr_user)
        self.assertEqual(stats['total_employees'], 1)

    def test_présences_aujourd_hui_filtrées_par_rôle(self):
        # Admin : emp1 + emp3 présents → 2
        stats_admin = self._stats(self.admin)
        self.assertEqual(stats_admin['present_today'], 2)

        # Entreprise dept1 : seulement emp1 → 1
        stats_ent = self._stats(self.ent_user)
        self.assertEqual(stats_ent['present_today'], 1)

    def test_non_authentifié_retourne_401(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 401)


# ===========================
# 12. Tests du Changement de Mot de Passe
# ===========================

class TestChangePasswordAPI(APITestCase):
    """ChangePasswordView valide l'ancien mot de passe et applique le nouveau"""

    url = '/api/auth/change-password/'

    def setUp(self):
        self.user = make_regular_user('chgpwd_user')

    def test_changement_valide(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {
            'old_password': 'emp123',
            'new_password': 'nouveauMDP456',
        })
        self.assertEqual(resp.status_code, 200)
        # Le nouveau mot de passe fonctionne pour s'authentifier
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('nouveauMDP456'))

    def test_ancien_mot_de_passe_incorrect_retourne_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {
            'old_password': 'mauvais',
            'new_password': 'nouveauMDP456',
        })
        self.assertEqual(resp.status_code, 400)
        # Le mot de passe original est inchangé
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('emp123'))

    def test_nouveau_mot_de_passe_trop_court_retourne_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {
            'old_password': 'emp123',
            'new_password': 'abc',
        })
        self.assertEqual(resp.status_code, 400)

    def test_champs_manquants_retournent_400(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.post(self.url, {'old_password': 'emp123'})
        self.assertEqual(resp.status_code, 400)

    def test_non_authentifié_retourne_401(self):
        resp = self.client.post(self.url, {
            'old_password': 'emp123',
            'new_password': 'nouveauMDP456',
        })
        self.assertEqual(resp.status_code, 401)
