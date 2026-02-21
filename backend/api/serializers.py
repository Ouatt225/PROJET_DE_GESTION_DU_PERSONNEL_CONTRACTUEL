"""
Serializers DRF pour l'API REST du système de gestion du personnel contractuel.

Chaque serializer transforme les instances de modèle Django en représentations
JSON (et inversement) pour les échanges avec le frontend.

Serializers disponibles :
  DirectionSerializer     — Direction (id, name uniquement)
  PasswordRecordSerializer — Mot de passe chiffré, exposé déchiffré via get_password_plain
  UserSerializer          — Utilisateur Django (lecture)
  DepartmentSerializer    — Entreprise prestataire avec compteur d'employés
  EmployeeSerializer      — Agent contractuel avec données calculées (âge, solde congés)
  LeaveSerializer         — Demande de congé avec validation des dates et du solde
  AttendanceSerializer    — Pointage avec validation check_in < check_out
  RegisterSerializer      — Création de compte avec confirmation de mot de passe

Conventions :
  - Les champs en lecture seule sont déclarés dans read_only_fields ou via ReadOnlyField.
  - Les champs calculés (propriétés du modèle) sont exposés via SerializerMethodField
    ou ReadOnlyField.
  - La validation métier est centralisée dans validate() ou validate_<field>().
"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Direction, Department, Employee, Leave, Attendance, PasswordRecord, LeaveNotification


class DirectionSerializer(serializers.ModelSerializer):
    """Serializer minimal pour le modèle Direction.

    Expose uniquement l'identifiant et le nom, suffisants pour alimenter
    les listes déroulantes du formulaire de création de manager.
    """

    class Meta:
        model = Direction
        fields = ['id', 'name']


class PasswordRecordSerializer(serializers.ModelSerializer):
    """Serializer pour la table des mots de passe.

    Le champ `password_plain` est calculé dynamiquement via get_password()
    (déchiffrement Fernet) et exposé en lecture seule.
    Les données de l'utilisateur (username, email, nom complet) sont dénormalisées
    pour faciliter l'affichage dans l'interface d'administration.

    Champs calculés :
        username (str)      : Identifiant de connexion de l'utilisateur.
        full_name (str)     : Nom complet ou username si le nom est vide.
        email (str)         : Adresse e-mail de l'utilisateur.
        direction (str)     : Direction de l'employé associé ('-' si N/A).
        department_name (str): Nom de l'entreprise de l'employé ('-' si N/A).
        password_plain (str): Mot de passe déchiffré (lecture seule).
    """

    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.SerializerMethodField()
    email = serializers.CharField(source='user.email', read_only=True)
    direction = serializers.SerializerMethodField()
    department_name = serializers.SerializerMethodField()
    password_plain = serializers.SerializerMethodField()

    class Meta:
        model = PasswordRecord
        fields = [
            'id', 'username', 'full_name', 'email', 'password_plain',
            'role', 'direction', 'department_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_password_plain(self, obj):
        """Retourne le mot de passe déchiffré via Fernet.

        Args:
            obj (PasswordRecord): Instance du modèle.

        Returns:
            str: Mot de passe en clair, ou '(indéchiffrable)' si la valeur
                 stockée n'est pas un token Fernet valide.
        """
        return obj.get_password()

    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur, ou son username si vide.

        Args:
            obj (PasswordRecord): Instance du modèle.

        Returns:
            str: Nom complet ('Prénom Nom') ou username.
        """
        name = obj.user.get_full_name()
        return name if name else obj.user.username

    def get_direction(self, obj):
        """Retourne la direction de l'employé associé à cet utilisateur.

        Args:
            obj (PasswordRecord): Instance du modèle.

        Returns:
            str: Nom de la direction, ou '-' si l'utilisateur n'a pas de profil employé.
        """
        try:
            employee = obj.user.employee_profile
            return employee.direction or '-'
        except Employee.DoesNotExist:
            return '-'

    def get_department_name(self, obj):
        """Retourne le nom de l'entreprise de l'employé associé.

        Args:
            obj (PasswordRecord): Instance du modèle.

        Returns:
            str: Nom de l'entreprise, ou '-' si l'utilisateur n'a pas de profil employé.
        """
        try:
            employee = obj.user.employee_profile
            return employee.department.name if employee.department else '-'
        except Employee.DoesNotExist:
            return '-'


class UserSerializer(serializers.ModelSerializer):
    """Serializer en lecture seule pour le modèle User Django.

    Utilisé pour dénormaliser les informations de l'utilisateur dans d'autres
    serializers (ex. EmployeeSerializer.user_details).
    """

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer pour les entreprises prestataires (Department).

    Le champ `employees_count` est exposé via la propriété du modèle
    et est automatiquement en lecture seule (ReadOnlyField).
    """

    employees_count = serializers.ReadOnlyField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'manager', 'description', 'employees_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer complet pour les agents contractuels.

    Expose toutes les données personnelles, professionnelles et calculées
    d'un employé. Les champs calculés incluent l'âge, l'année de retraite
    et les informations de gestion des congés.

    Champs calculés :
        full_name (str)                 : Prénom + Nom (propriété du modèle).
        department_name (str)           : Nom de l'entreprise (FK dénormalisée).
        user_details (dict)             : Données complètes du User associé.
        cnps_number (str)               : Alias du champ cnps (compatibilité frontend).
        leave_balance (int)             : Solde de congés payés restants.
        leaves_taken_this_year (int)    : Jours de congés payés approuvés cette année.
        leaves_pending_this_year (int)  : Jours de congés payés en attente.
        annual_leave_allowance (int)    : Quota annuel fixe (ANNUAL_LEAVE_ALLOWANCE).
        age (int|None)                  : Âge calculé depuis birth_date.
        retirement_year (int|None)      : Année de départ à la retraite (birth_date + 60).

    Validations :
        email      : Unicité vérifiée en création et édition.
        birth_date : L'employé doit avoir entre 18 et 60 ans.
    """

    full_name = serializers.ReadOnlyField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    # Alias pour la compatibilité avec certains formulaires frontend
    cnps_number = serializers.CharField(source='cnps', required=True)
    # Champs de gestion des congés
    leave_balance = serializers.ReadOnlyField()
    leaves_taken_this_year = serializers.ReadOnlyField()
    leaves_pending_this_year = serializers.ReadOnlyField()
    annual_leave_allowance = serializers.SerializerMethodField()
    # Champs calculés démographiques
    age = serializers.SerializerMethodField()
    retirement_year = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'matricule', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'birth_date', 'gender', 'department', 'department_name', 'direction', 'position', 'hire_date',
            'salary', 'cnps', 'cnps_number', 'city', 'commune', 'address',
            'marital_status', 'number_of_children', 'status', 'user', 'user_details',
            'photo', 'cni_recto', 'cni_verso',
            'leave_balance', 'leaves_taken_this_year', 'leaves_pending_this_year',
            'annual_leave_allowance', 'age', 'retirement_year', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'phone': {'required': True, 'allow_blank': False, 'allow_null': False},
            'matricule': {'required': True, 'allow_blank': False, 'allow_null': False},
            'cnps': {'required': True, 'allow_blank': False, 'allow_null': False},
            'address': {'required': True, 'allow_blank': False, 'allow_null': False},
        }

    def get_annual_leave_allowance(self, obj):
        """Retourne le quota annuel de congés payés (constante de classe).

        Args:
            obj (Employee): Instance de l'employé.

        Returns:
            int: ANNUAL_LEAVE_ALLOWANCE (30 jours).
        """
        return Employee.ANNUAL_LEAVE_ALLOWANCE

    def get_age(self, obj):
        """Calcule l'âge de l'employé à partir de sa date de naissance.

        Args:
            obj (Employee): Instance de l'employé.

        Returns:
            int|None: Âge en années entières, ou None si birth_date est absent.
        """
        if obj.birth_date:
            from datetime import date
            today = date.today()
            age = today.year - obj.birth_date.year - (
                (today.month, today.day) < (obj.birth_date.month, obj.birth_date.day)
            )
            return age
        return None

    def get_retirement_year(self, obj):
        """Calcule l'année prévue de départ à la retraite (âge légal : 60 ans).

        Args:
            obj (Employee): Instance de l'employé.

        Returns:
            int|None: Année de retraite (birth_date.year + 60), ou None si absence de birth_date.
        """
        if obj.birth_date:
            return obj.birth_date.year + 60
        return None

    def validate_email(self, value):
        """Vérifie l'unicité de l'email en création et en édition.

        En mode édition (instance existante), l'email de l'instance courante
        est exclu de la vérification pour permettre de sauvegarder sans modifier l'email.

        Args:
            value (str): Adresse e-mail saisie.

        Returns:
            str: Email validé.

        Raises:
            serializers.ValidationError: Si l'email est déjà utilisé par un autre employé.
        """
        instance = self.instance
        if instance:
            if Employee.objects.exclude(pk=instance.pk).filter(email=value).exists():
                raise serializers.ValidationError("Cet email est déjà utilisé par un autre employé.")
        else:
            if Employee.objects.filter(email=value).exists():
                raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_birth_date(self, value):
        """Vérifie que l'employé a entre 18 et 60 ans à la date du jour.

        La limite à 60 ans correspond à l'âge légal de la retraite.

        Args:
            value (date): Date de naissance saisie.

        Returns:
            date: Date de naissance validée.

        Raises:
            serializers.ValidationError: Si l'âge calculé est inférieur à 18
                ou supérieur ou égal à 60 ans.
        """
        if value:
            from datetime import date
            today = date.today()
            age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))

            if age < 18:
                raise serializers.ValidationError(
                    f"L'employé doit avoir au moins 18 ans. Âge calculé: {age} ans."
                )
            if age >= 60:
                raise serializers.ValidationError(
                    f"L'employé doit avoir moins de 60 ans (âge de la retraite). Âge calculé: {age} ans."
                )
        return value


class LeaveSerializer(serializers.ModelSerializer):
    """Serializer pour les demandes de congé.

    Dénormalise le nom de l'employé et des approbateurs pour l'affichage.
    Effectue deux validations métier critiques :
      1. La date de fin doit être postérieure ou égale à la date de début.
      2. Pour les congés payés, le solde disponible (après soustraction des
         demandes en attente) doit couvrir la durée demandée.

    Champs calculés :
        employee_name (str)           : Nom complet de l'employé.
        days_count (int)              : Nombre de jours (propriété du modèle).
        manager_approved_by_name (str): Nom du manager validateur.
        approved_by_name (str)        : Nom de l'approbateur final.
    """

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    days_count = serializers.ReadOnlyField()
    manager_approved_by_name = serializers.CharField(source='manager_approved_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)

    class Meta:
        model = Leave
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'start_date',
            'end_date', 'days_count', 'reason', 'status',
            'manager_approved_by', 'manager_approved_by_name',
            'approved_by', 'approved_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'reason': {'required': True, 'allow_blank': False, 'allow_null': False},
        }

    def validate(self, data):
        """Valide les dates de congé et le solde de congés payés disponible.

        Vérifications effectuées :
          1. end_date >= start_date.
          2. Pour leave_type='paid' : le solde effectif (balance - jours en attente)
             doit être supérieur ou égal au nombre de jours demandés.

        Args:
            data (dict): Données désérialisées du formulaire.

        Returns:
            dict: Données validées inchangées.

        Raises:
            serializers.ValidationError: Si les dates sont invalides ou
                si le solde de congés est insuffisant.
        """
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError({
                    'end_date': "La date de fin doit être postérieure à la date de début."
                })

            days_requested = (data['end_date'] - data['start_date']).days + 1

            # Vérifier le solde uniquement pour les congés payés
            employee = data.get('employee')
            if employee and data.get('leave_type') == 'paid':
                available_balance = employee.leave_balance
                pending_days = employee.leaves_pending_this_year

                # Solde effectif = solde disponible moins les jours déjà en attente
                effective_balance = available_balance - pending_days

                if days_requested > effective_balance:
                    raise serializers.ValidationError({
                        'end_date': f"Solde de congés insuffisant. Vous avez {available_balance} jours disponibles "
                                   f"({pending_days} jours en attente d'approbation). "
                                   f"Vous demandez {days_requested} jours."
                    })

        return data


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer pour les enregistrements de présence (pointages).

    Le champ `hours_worked` est calculé côté modèle à partir de check_in et check_out.
    La validation s'assure que l'heure de sortie est postérieure à l'heure d'entrée.

    Champs calculés :
        employee_name (str): Nom complet de l'employé.
        hours_worked (float): Heures travaillées (propriété du modèle).
    """

    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    hours_worked = serializers.ReadOnlyField()

    class Meta:
        model = Attendance
        fields = [
            'id', 'employee', 'employee_name', 'date', 'check_in',
            'check_out', 'hours_worked', 'status', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Valide que l'heure de sortie est postérieure à l'heure d'entrée.

        Args:
            data (dict): Données désérialisées.

        Returns:
            dict: Données validées inchangées.

        Raises:
            serializers.ValidationError: Si check_out <= check_in.
        """
        if data.get('check_in') and data.get('check_out'):
            if data['check_out'] <= data['check_in']:
                raise serializers.ValidationError({
                    'check_out': "L'heure de sortie doit être postérieure à l'heure d'entrée."
                })
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'un nouveau compte utilisateur.

    Inclut la confirmation de mot de passe (password2) et l'attribution
    d'un rôle. Les permissions Django (is_staff, is_superuser) sont
    définies automatiquement selon le rôle choisi.

    Fields:
        password (str)  : Mot de passe (write_only).
        password2 (str) : Confirmation du mot de passe (write_only).
        role (str)      : 'admin' | 'manager' | 'entreprise' | 'employee' (optionnel, défaut: 'employee').
    """

    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=['admin', 'manager', 'entreprise', 'employee'], required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name', 'role']

    def validate(self, attrs):
        """Vérifie que les deux mots de passe correspondent.

        Args:
            attrs (dict): Données désérialisées.

        Returns:
            dict: Données validées.

        Raises:
            serializers.ValidationError: Si password != password2.
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        """Crée l'utilisateur et configure ses permissions selon le rôle.

        Supprime password2 des données avant création.
        Définit is_staff=True pour 'manager' et is_superuser=True pour 'admin'.

        Args:
            validated_data (dict): Données validées (sans erreurs).

        Returns:
            User: Instance de l'utilisateur Django créé.
        """
        validated_data.pop('password2')
        role = validated_data.pop('role', 'employee')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )

        # Définir les permissions Django selon le rôle
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'manager':
            user.is_staff = True

        user.save()
        return user


class LeaveNotificationSerializer(serializers.ModelSerializer):
    """Serializer pour les alarmes de rappel de congés.

    Dénormalise les informations du congé et de l'employé pour
    affichage direct dans la liste des notifications frontend.

    Champs calculés :
        employee_name (str)      : Nom complet de l'employé concerné.
        leave_start_date (date)  : Date de début du congé.
        leave_type_display (str) : Libellé du type de congé.
        notification_type_display (str): Libellé du type d'alarme.
        days_until_start (int)   : Jours restants avant le début du congé.
    """

    employee_name = serializers.CharField(
        source='leave.employee.full_name', read_only=True
    )
    leave_start_date = serializers.DateField(
        source='leave.start_date', read_only=True
    )
    leave_end_date = serializers.DateField(
        source='leave.end_date', read_only=True
    )
    leave_type_display = serializers.CharField(
        source='leave.get_leave_type_display', read_only=True
    )
    notification_type_display = serializers.CharField(
        source='get_notification_type_display', read_only=True
    )
    days_until_start = serializers.SerializerMethodField()

    class Meta:
        model = LeaveNotification
        fields = [
            'id', 'leave', 'notification_type', 'notification_type_display',
            'trigger_date', 'is_read', 'created_at',
            'employee_name', 'leave_start_date', 'leave_end_date',
            'leave_type_display', 'days_until_start',
        ]
        read_only_fields = ['id', 'created_at', 'trigger_date', 'notification_type']

    def get_days_until_start(self, obj):
        """Retourne le nombre de jours restants avant le début du congé.

        Returns:
            int: Jours restants (peut être négatif si le congé a déjà commencé).
        """
        from datetime import date
        return (obj.leave.start_date - date.today()).days
