"""
Vues et ViewSets de l'API REST du système de gestion du personnel contractuel.

Architecture :
  get_user_context(user)  — Fonction utilitaire déterminant le rôle et le périmètre
                            d'accès d'un utilisateur (admin / entreprise / manager / employee).

  RoleFilterMixin         — Mixin générique appliquant le filtrage par rôle sur n'importe
                            quel queryset, configurable via des attributs de classe.

  ViewSets (CRUD complet) :
    DirectionViewSet       — Directions (lecture seule)
    PasswordRecordViewSet  — Mots de passe chiffrés (admins uniquement)
    DepartmentViewSet      — Entreprises prestataires
    EmployeeViewSet        — Agents contractuels
    LeaveViewSet           — Demandes de congé (avec workflow d'approbation)
    AttendanceViewSet      — Pointages de présence

  APIViews (endpoints dédiés) :
    RegisterView           — Création de compte utilisateur
    LoginView              — Authentification JWT avec enrichissement du payload
    ChangePasswordView     — Modification du mot de passe authentifié
    DashboardStatsView     — Statistiques filtrées par rôle pour le tableau de bord

Authentification : JWT (djangorestframework-simplejwt).
Autorisation     : Basée sur les champs is_staff, is_superuser et les profils
                   ManagerProfile / CompanyProfile.
"""

import logging

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView, exception_handler as drf_exception_handler
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Direction, ManagerProfile, CompanyProfile, Department, Employee, Leave, Attendance, PasswordRecord
from .serializers import (
    DirectionSerializer, PasswordRecordSerializer, DepartmentSerializer, EmployeeSerializer,
    LeaveSerializer, AttendanceSerializer,
    RegisterSerializer, UserSerializer
)

logger = logging.getLogger('api')
security_logger = logging.getLogger('api.security')


def custom_exception_handler(exc, context):
    """Gestionnaire d'exceptions global pour Django REST Framework.

    Étend le handler DRF par défaut pour :
      - Logger les erreurs inattendues (non gérées par DRF) avec traceback complet.
      - Retourner un JSON structuré ``{"error": "..."}`` pour les erreurs 500
        afin d'éviter d'exposer des détails d'implémentation au client.

    Args:
        exc (Exception): L'exception levée.
        context (dict): Contexte DRF contenant la view et la request.

    Returns:
        Response: Réponse DRF standard, ou réponse 500 structurée si l'exception
                  n'était pas gérée par DRF.
    """
    response = drf_exception_handler(exc, context)

    if response is None:
        # Exception non gérée par DRF (ex. erreur DB, AttributeError inattendue)
        view_name = context['view'].__class__.__name__ if context.get('view') else 'unknown'
        method = context['request'].method if context.get('request') else 'unknown'
        logger.error(
            "Erreur interne non gérée dans %s.%s : %s",
            view_name, method, str(exc),
            exc_info=True,
        )
        return Response(
            {"error": "Une erreur interne est survenue. Veuillez réessayer."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Log les erreurs serveur 5xx qui ont été gérées par DRF
    if response.status_code >= 500:
        logger.error("Erreur serveur %s : %s", response.status_code, response.data)

    return response


class LoginRateThrottle(AnonRateThrottle):
    """Limite les tentatives de connexion à 10 par minute et par IP.

    Protège l'endpoint ``/api/login/`` contre les attaques par force brute.
    Le scope 'login' doit être configuré dans ``REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']``.
    """

    scope = 'login'


def get_user_context(user):
    """Détermine le rôle et les ressources accessibles d'un utilisateur.

    Inspecte les champs Django (is_superuser, is_staff) et les profils
    personnalisés (CompanyProfile, ManagerProfile) pour retourner un
    dictionnaire de contexte utilisé par les ViewSets pour filtrer les données.

    Priorité de détection :
      1. Superuser → admin
      2. Possède un CompanyProfile → entreprise
      3. is_staff → manager (avec liste des directions gérées)
      4. Sinon → employee

    Args:
        user (User): Instance de l'utilisateur Django authentifié.

    Returns:
        dict: Dictionnaire contenant au minimum la clé 'role', et selon le rôle :
            - {'role': 'admin'}
            - {'role': 'entreprise', 'department': Department}
            - {'role': 'manager', 'directions': list[str]}
            - {'role': 'employee'}
    """
    if user.is_superuser:
        return {'role': 'admin'}

    try:
        company = user.company_profile
        return {'role': 'entreprise', 'department': company.department}
    except CompanyProfile.DoesNotExist:
        pass

    if user.is_staff:
        try:
            direction_names = list(user.manager_profile.directions.values_list('name', flat=True))
        except ManagerProfile.DoesNotExist:
            direction_names = []
        return {'role': 'manager', 'directions': direction_names}

    return {'role': 'employee'}


class RoleFilterMixin:
    """Mixin réutilisable pour le filtrage des querysets selon le rôle utilisateur.

    Centralise la logique de filtrage RBAC (Role-Based Access Control) applicable
    à tout ViewSet dont les objets sont liés à des employés.

    Les champs de filtre sont configurables par attributs de classe, ce qui permet
    à chaque ViewSet d'adapter les noms de champs sans dupliquer la logique.

    Attributes:
        company_filter_field (str): Champ ORM pour filtrer par entreprise.
            Défaut : 'employee__department'.
        direction_filter_field (str): Champ ORM pour filtrer par direction (lookup __in).
            Défaut : 'employee__direction__in'.
        employee_filter_field (str): Champ ORM pour filtrer par utilisateur employé.
            Défaut : 'employee__user'.

    Usage:
        class MonViewSet(RoleFilterMixin, viewsets.ModelViewSet):
            company_filter_field = 'department'      # override si nécessaire
            direction_filter_field = 'direction__in'
            employee_filter_field = 'user'

            def get_queryset(self):
                return self.get_role_filtered_queryset(MonModel.objects.all())
    """

    company_filter_field = 'employee__department'
    direction_filter_field = 'employee__direction__in'
    employee_filter_field = 'employee__user'

    def get_role_filtered_queryset(self, queryset):
        """Filtre le queryset selon le rôle de l'utilisateur authentifié.

        Args:
            queryset (QuerySet): Queryset de base non filtré.

        Returns:
            QuerySet: Queryset filtré selon le rôle et le périmètre de l'utilisateur.
                - admin     → queryset complet (aucun filtre)
                - entreprise → filtrée par entreprise (company_filter_field)
                - manager   → filtrée par directions (direction_filter_field),
                              ou queryset vide si le manager n'a aucune direction
                - employee  → filtrée par l'utilisateur lui-même (employee_filter_field)
        """
        ctx = get_user_context(self.request.user)
        role = ctx['role']

        if role == 'admin':
            return queryset
        if role == 'entreprise':
            return queryset.filter(**{self.company_filter_field: ctx['department']})
        if role == 'manager':
            if ctx['directions']:
                return queryset.filter(**{self.direction_filter_field: ctx['directions']})
            return queryset.none()
        # Rôle employee : accès limité à ses propres données
        return queryset.filter(**{self.employee_filter_field: self.request.user})


class DirectionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet en lecture seule pour les directions ministérielles.

    Utilisé principalement pour alimenter les listes déroulantes dans l'interface.
    Accessible à tout utilisateur authentifié.
    La pagination est désactivée (retour de la liste complète).
    """

    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None


class PasswordRecordViewSet(viewsets.ModelViewSet):
    """ViewSet pour la consultation et la gestion des mots de passe chiffrés.

    Accès restreint aux utilisateurs avec is_staff=True (admins et managers).
    Les mots de passe sont retournés déchiffrés par le serializer (champ password_plain).

    Filtrage par rôle :
        - admin     → tous les enregistrements
        - entreprise → enregistrements des employés de son entreprise
        - manager   → enregistrements des employés de ses directions
        - employee  → aucun accès (HTTP 403)
    """

    queryset = PasswordRecord.objects.all()
    serializer_class = PasswordRecordSerializer
    permission_classes = [permissions.IsAdminUser]
    search_fields = ['user__first_name', 'user__last_name', 'user__username', 'role']
    ordering_fields = ['user__last_name', 'role', 'created_at']
    pagination_class = None

    def get_queryset(self):
        """Retourne les enregistrements de mots de passe accessibles à l'utilisateur.

        Returns:
            QuerySet[PasswordRecord]: Queryset filtré selon le rôle.
        """
        ctx = get_user_context(self.request.user)
        role = ctx['role']

        if role == 'admin':
            return PasswordRecord.objects.all()
        if role == 'entreprise':
            employee_users = Employee.objects.filter(
                department=ctx['department']
            ).values_list('user', flat=True)
            return PasswordRecord.objects.filter(user__in=employee_users)
        if role == 'manager':
            if ctx['directions']:
                employee_users = Employee.objects.filter(
                    direction__in=ctx['directions']
                ).values_list('user', flat=True)
                return PasswordRecord.objects.filter(user__in=employee_users)
            return PasswordRecord.objects.all()
        return PasswordRecord.objects.none()


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet CRUD pour les entreprises prestataires (Department).

    Filtrage par rôle :
        - admin / manager → toutes les entreprises
        - entreprise      → uniquement la sienne
        - employee        → uniquement l'entreprise à laquelle il est rattaché

    La pagination est désactivée (retour de la liste complète).
    """

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        """Retourne les entreprises visibles par l'utilisateur authentifié.

        Returns:
            QuerySet[Department]: Queryset filtré selon le rôle.
        """
        ctx = get_user_context(self.request.user)
        role = ctx['role']

        if role in ('admin', 'manager'):
            return Department.objects.all()
        if role == 'entreprise':
            return Department.objects.filter(id=ctx['department'].id)
        # employee : accès limité à son entreprise de rattachement
        try:
            emp = self.request.user.employee_profile
            if emp.department:
                return Department.objects.filter(id=emp.department.id)
        except Employee.DoesNotExist:
            pass
        return Department.objects.none()

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Récupère tous les employés rattachés à une entreprise donnée.

        Args:
            request (Request): Requête HTTP.
            pk (str): Clé primaire de l'entreprise.

        Returns:
            Response: Liste sérialisée des employés de l'entreprise.
        """
        department = self.get_object()
        employees = department.employees.all()
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)


class EmployeeViewSet(RoleFilterMixin, viewsets.ModelViewSet):
    """ViewSet CRUD pour les agents contractuels.

    Hérite de RoleFilterMixin avec des champs de filtre adaptés au modèle Employee
    (les champs ne sont pas préfixés par 'employee__' puisque Employee est la
    ressource principale).

    Champs de filtre surchargés :
        company_filter_field   = 'department'
        direction_filter_field = 'direction__in'
        employee_filter_field  = 'user'

    La pagination est désactivée (retour de la liste complète).
    """

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None
    filterset_fields = ['department', 'status', 'position']
    search_fields = ['first_name', 'last_name', 'email', 'position']
    ordering_fields = ['created_at', 'hire_date', 'last_name']

    # Champs de filtre adaptés au modèle Employee (ressource principale)
    company_filter_field = 'department'
    direction_filter_field = 'direction__in'
    employee_filter_field = 'user'

    def get_queryset(self):
        """Retourne les employés accessibles à l'utilisateur authentifié.

        Returns:
            QuerySet[Employee]: Queryset filtré par RoleFilterMixin.
        """
        return self.get_role_filtered_queryset(Employee.objects.all())

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """Retourne les employés regroupés par entreprise.

        Chaque entrée du tableau contient les données de l'entreprise et la liste
        de ses employés (sérialisée). N'inclut que les entreprises ayant au moins
        un employé visible par l'utilisateur courant.

        Args:
            request (Request): Requête HTTP.

        Returns:
            Response: Liste de dicts {'department': {...}, 'employees': [...]}.
        """
        departments = Department.objects.all()
        employee_qs = self.get_queryset()
        result = []
        for dept in departments:
            dept_employees = employee_qs.filter(department=dept)
            if dept_employees.exists():
                result.append({
                    'department': DepartmentSerializer(dept).data,
                    'employees': EmployeeSerializer(dept_employees, many=True).data
                })
        return Response(result)


class LeaveViewSet(RoleFilterMixin, viewsets.ModelViewSet):
    """ViewSet CRUD pour les demandes de congé, avec workflow d'approbation à deux niveaux.

    Workflow d'approbation :
      Employee soumet (POST /leaves/)       → status = 'pending'
      Manager valide (POST /leaves/{id}/approve/) → status = 'manager_approved'
      Entreprise approuve (POST /leaves/{id}/approve/) → status = 'approved'
      Tout rôle autorisé (POST /leaves/{id}/reject/)   → status = 'rejected'

    L'admin peut approuver directement (court-circuit des deux étapes).
    La suppression est interdite pour les congés déjà approuvés.
    """

    queryset = Leave.objects.all()
    pagination_class = None
    serializer_class = LeaveSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['employee', 'status', 'leave_type']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['created_at', 'start_date']

    def get_queryset(self):
        """Retourne les demandes de congé accessibles à l'utilisateur authentifié.

        Returns:
            QuerySet[Leave]: Queryset filtré par RoleFilterMixin.
        """
        return self.get_role_filtered_queryset(Leave.objects.all())

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approuve ou valide une demande de congé selon le rôle de l'appelant.

        Comportement selon le rôle :
          - admin     : approbation directe (status → 'approved')
          - manager   : première validation (status → 'manager_approved')
          - entreprise : validation finale si manager_approved (status → 'approved')

        Args:
            request (Request): Requête HTTP POST.
            pk (str): Identifiant de la demande de congé.

        Returns:
            Response: Données du congé mis à jour (HTTP 200), ou erreur (HTTP 400).
        """
        leave = self.get_object()
        user = request.user

        if user.is_superuser:
            # Admin : approbation directe, bypasse la validation manager
            leave.status = 'approved'
            leave.approved_by = user
            if not leave.manager_approved_by:
                leave.manager_approved_by = user
        else:
            is_entreprise = False
            try:
                user.company_profile
                is_entreprise = True
            except CompanyProfile.DoesNotExist:
                pass

            if is_entreprise:
                # L'entreprise ne peut valider que si le manager a déjà approuvé
                if leave.status != 'manager_approved':
                    return Response(
                        {"error": "Ce congé doit d'abord être validé par le manager de direction."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                leave.status = 'approved'
                leave.approved_by = user
            elif user.is_staff:
                # Manager : première validation uniquement si le congé est en attente
                if leave.status != 'pending':
                    return Response(
                        {"error": "Ce congé n'est plus en attente de validation manager."},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                leave.status = 'manager_approved'
                leave.manager_approved_by = user

        leave.save()
        logger.info(
            "Congé #%s approuvé (status=%s) par user='%s'",
            leave.pk, leave.status, request.user.username,
        )
        serializer = self.get_serializer(leave)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejette une demande de congé (status → 'rejected').

        Seuls les utilisateurs avec is_staff ou is_superuser peuvent rejeter.
        Un congé déjà approuvé ou rejeté ne peut pas être retraité.

        Args:
            request (Request): Requête HTTP POST.
            pk (str): Identifiant de la demande de congé.

        Returns:
            Response: Données du congé mis à jour (HTTP 200), ou erreur
                (HTTP 403 si non autorisé, HTTP 400 si déjà traité).
        """
        user = request.user
        if not user.is_staff and not user.is_superuser:
            return Response(
                {"error": "Vous n'avez pas la permission de rejeter un congé."},
                status=status.HTTP_403_FORBIDDEN
            )
        leave = self.get_object()
        if leave.status in ('approved', 'rejected'):
            return Response(
                {"error": "Ce congé a déjà été traité."},
                status=status.HTTP_400_BAD_REQUEST
            )
        leave.status = 'rejected'
        leave.approved_by = user
        leave.save()
        logger.info(
            "Congé #%s rejeté par user='%s'",
            leave.pk, user.username,
        )
        serializer = self.get_serializer(leave)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        """Supprime une demande de congé.

        La suppression est interdite si le congé est dans le statut 'approved'.

        Returns:
            Response: HTTP 204 si suppression réussie,
                      HTTP 400 si le congé est déjà approuvé.
        """
        leave = self.get_object()
        if leave.status == 'approved':
            return Response(
                {"error": "Impossible de supprimer un congé déjà approuvé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Retourne toutes les demandes en attente de traitement.

        Inclut les statuts 'pending' (attente manager) et 'manager_approved'
        (attente approbation entreprise).

        Args:
            request (Request): Requête HTTP GET.

        Returns:
            Response: Liste des demandes de congé non finalisées.
        """
        pending_leaves = self.get_queryset().filter(status__in=['pending', 'manager_approved'])
        serializer = self.get_serializer(pending_leaves, many=True)
        return Response(serializer.data)


class AttendanceViewSet(RoleFilterMixin, viewsets.ModelViewSet):
    """ViewSet CRUD pour les enregistrements de présence (pointages).

    La contrainte unique_together (employee, date) est gérée au niveau du modèle.
    Le calcul des heures travaillées est délégué à la propriété Attendance.hours_worked.
    """

    queryset = Attendance.objects.all()
    pagination_class = None
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['employee', 'status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering_fields = ['date']

    def get_queryset(self):
        """Retourne les présences accessibles à l'utilisateur authentifié.

        Returns:
            QuerySet[Attendance]: Queryset filtré par RoleFilterMixin.
        """
        return self.get_role_filtered_queryset(Attendance.objects.all())

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Retourne les enregistrements de présence pour la date du jour.

        Args:
            request (Request): Requête HTTP GET.

        Returns:
            Response: Liste des présences d'aujourd'hui.
        """
        from datetime import date
        today_attendance = self.queryset.filter(date=date.today())
        serializer = self.get_serializer(today_attendance, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_employee(self, request):
        """Retourne l'historique de présence d'un employé donné.

        Args:
            request (Request): Requête HTTP GET avec query param `employee_id`.

        Returns:
            Response: Liste des présences de l'employé (HTTP 200),
                      ou HTTP 400 si employee_id manquant.
        """
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {"error": "employee_id est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendances = self.queryset.filter(employee_id=employee_id)
        serializer = self.get_serializer(attendances, many=True)
        return Response(serializer.data)


class RegisterView(APIView):
    """Vue pour la création d'un nouveau compte utilisateur.

    Accessible sans authentification (AllowAny).
    Retourne les tokens JWT (access + refresh) et les données de l'utilisateur créé.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Crée un compte utilisateur et retourne les tokens JWT.

        Args:
            request (Request): Corps JSON avec username, password, password2,
                email, first_name, last_name, role.

        Returns:
            Response: {'user': {...}, 'refresh': str, 'access': str} (HTTP 201),
                      ou erreurs de validation (HTTP 400).
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Vue d'authentification personnalisée retournant les tokens JWT enrichis.

    Le payload retourné inclut, en plus des tokens standard, des informations
    sur le rôle et le périmètre de l'utilisateur :
      - role              : 'admin' | 'manager' | 'entreprise' | 'employee'
      - managed_directions : liste des noms de directions (pour managers)
      - managed_department : {'id', 'name'} de l'entreprise (pour entreprise)

    Accessible sans authentification (AllowAny).
    Protégée par LoginRateThrottle (10 tentatives/minute par IP).
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        """Authentifie un utilisateur et retourne les tokens JWT avec métadonnées de rôle.

        Le rôle et le périmètre (directions/département) sont déterminés via
        ``get_user_context()`` pour éviter toute duplication de logique.
        Les tentatives échouées sont journalisées dans le log de sécurité.

        Args:
            request (Request): Corps JSON avec username et password.

        Returns:
            Response: {'user': {...}, 'refresh': str, 'access': str} (HTTP 200),
                      {'error': '...'} (HTTP 400 si champs manquants),
                      ou {'error': 'Identifiants invalides'} (HTTP 401).
        """
        username = request.data.get('username')
        password = request.data.get('password')
        ip = request.META.get('REMOTE_ADDR', 'inconnu')

        if not username or not password:
            return Response(
                {"error": "Le nom d'utilisateur et le mot de passe sont requis."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is not None:
            # Déléguer entièrement la détection de rôle et de périmètre à get_user_context()
            ctx = get_user_context(user)
            role = ctx['role']

            # Construire les métadonnées de périmètre depuis le contexte centralisé
            managed_directions = ctx.get('directions', [])
            managed_department = None
            if role == 'entreprise':
                dept = ctx.get('department')
                if dept:
                    managed_department = {'id': dept.id, 'name': dept.name}

            refresh = RefreshToken.for_user(user)
            security_logger.info(
                "Connexion réussie : utilisateur='%s' rôle=%s ip=%s",
                user.username, role, ip,
            )
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'name': user.get_full_name() or user.username,
                    'role': role,
                    'managed_directions': managed_directions,
                    'managed_department': managed_department,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            security_logger.warning(
                "Échec de connexion : username='%s' ip=%s",
                username, ip,
            )
            return Response(
                {"error": "Identifiants invalides"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class ChangePasswordView(APIView):
    """Vue permettant à un utilisateur authentifié de changer son mot de passe.

    Validations effectuées :
      - Les deux champs (old_password, new_password) doivent être fournis.
      - L'ancien mot de passe doit correspondre au mot de passe actuel.
      - Le nouveau mot de passe passe les validateurs Django (AUTH_PASSWORD_VALIDATORS) :
          longueur minimale, pas trop similaire au nom d'utilisateur,
          pas un mot de passe commun, pas entièrement numérique.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Change le mot de passe de l'utilisateur connecté.

        Args:
            request (Request): Corps JSON avec old_password et new_password.

        Returns:
            Response: {'message': 'Mot de passe modifié avec succès'} (HTTP 200),
                      ou {'error': str | list} (HTTP 400).
        """
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {"error": "Ancien et nouveau mot de passe requis"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(old_password):
            security_logger.warning(
                "Tentative de changement de mot de passe avec ancien mdp incorrect : user='%s'",
                user.username,
            )
            return Response(
                {"error": "Ancien mot de passe incorrect"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Valider le nouveau mot de passe via AUTH_PASSWORD_VALIDATORS (Django)
        try:
            validate_password(new_password, user)
        except DjangoValidationError as exc:
            return Response(
                {"error": list(exc.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save()
        security_logger.info("Mot de passe changé avec succès : user='%s'", user.username)
        return Response({"message": "Mot de passe modifié avec succès"})


class DashboardStatsView(APIView):
    """Vue retournant les statistiques du tableau de bord filtrées par rôle.

    Les métriques retournées sont scopées au périmètre visible par l'utilisateur :
      - admin     → toutes les données
      - entreprise → données de son entreprise uniquement
      - manager   → données de ses directions uniquement

    Métriques :
      - total_employees   : nombre d'agents dans le périmètre
      - total_departments : nombre total d'entreprises (non filtré par rôle)
      - present_today     : agents marqués 'present' aujourd'hui
      - on_leave_today    : agents en congé approuvé couvrant la date du jour
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Calcule et retourne les statistiques du tableau de bord.

        Args:
            request (Request): Requête HTTP GET authentifiée.

        Returns:
            Response: Dict avec total_employees, total_departments,
                      present_today, on_leave_today.
        """
        from datetime import date

        ctx = get_user_context(request.user)
        role = ctx['role']

        employees_qs = Employee.objects.all()
        leaves_qs = Leave.objects.all()
        attendance_qs = Attendance.objects.all()

        # Filtrer selon le périmètre du rôle
        if role == 'entreprise':
            dept = ctx['department']
            employees_qs = employees_qs.filter(department=dept)
            leaves_qs = leaves_qs.filter(employee__department=dept)
            attendance_qs = attendance_qs.filter(employee__department=dept)
        elif role == 'manager':
            directions = ctx['directions']
            if directions:
                employees_qs = employees_qs.filter(direction__in=directions)
                leaves_qs = leaves_qs.filter(employee__direction__in=directions)
                attendance_qs = attendance_qs.filter(employee__direction__in=directions)
            else:
                employees_qs = employees_qs.none()
                leaves_qs = leaves_qs.none()
                attendance_qs = attendance_qs.none()

        total_employees = employees_qs.count()
        # total_departments n'est pas filtré par rôle (vue globale de la structure)
        total_departments = Department.objects.count()
        present_today = attendance_qs.filter(
            date=date.today(),
            status='present'
        ).count()
        on_leave_today = leaves_qs.filter(
            start_date__lte=date.today(),
            end_date__gte=date.today(),
            status='approved'
        ).count()

        return Response({
            'total_employees': total_employees,
            'total_departments': total_departments,
            'present_today': present_today,
            'on_leave_today': on_leave_today,
        })
