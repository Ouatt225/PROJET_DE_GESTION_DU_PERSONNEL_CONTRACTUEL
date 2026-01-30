from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Department, Employee, Leave, Attendance


class UserSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle User"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Department"""
    employees_count = serializers.ReadOnlyField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'manager', 'description', 'employees_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Employee"""
    full_name = serializers.ReadOnlyField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    user_details = UserSerializer(source='user', read_only=True)
    # Alias pour la compatibilité frontend
    cnps_number = serializers.CharField(source='cnps', required=False, allow_blank=True, allow_null=True)
    # Champs pour la gestion des congés
    leave_balance = serializers.ReadOnlyField()
    leaves_taken_this_year = serializers.ReadOnlyField()
    leaves_pending_this_year = serializers.ReadOnlyField()
    annual_leave_allowance = serializers.SerializerMethodField()
    # Champs pour l'âge et la retraite
    age = serializers.SerializerMethodField()
    retirement_year = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id', 'first_name', 'last_name', 'full_name', 'email', 'phone',
            'birth_date', 'gender', 'department', 'department_name', 'position', 'hire_date',
            'salary', 'cnps', 'cnps_number', 'city', 'commune', 'address',
            'marital_status', 'number_of_children', 'status', 'user', 'user_details',
            'photo', 'cni_document',
            'leave_balance', 'leaves_taken_this_year', 'leaves_pending_this_year',
            'annual_leave_allowance', 'age', 'retirement_year', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_annual_leave_allowance(self, obj):
        return Employee.ANNUAL_LEAVE_ALLOWANCE

    def get_age(self, obj):
        """Calcule l'âge de l'employé"""
        if obj.birth_date:
            from datetime import date
            today = date.today()
            age = today.year - obj.birth_date.year - (
                (today.month, today.day) < (obj.birth_date.month, obj.birth_date.day)
            )
            return age
        return None

    def get_retirement_year(self, obj):
        """Calcule l'année de départ à la retraite (60 ans)"""
        if obj.birth_date:
            return obj.birth_date.year + 60
        return None

    def validate_email(self, value):
        """Valide l'unicité de l'email"""
        instance = self.instance
        if instance:
            # Mode édition
            if Employee.objects.exclude(pk=instance.pk).filter(email=value).exists():
                raise serializers.ValidationError("Cet email est déjà utilisé par un autre employé.")
        else:
            # Mode création
            if Employee.objects.filter(email=value).exists():
                raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value

    def validate_birth_date(self, value):
        """Valide que l'employé a entre 18 et 60 ans"""
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
    """Serializer pour le modèle Leave"""
    employee_name = serializers.CharField(source='employee.full_name', read_only=True)
    days_count = serializers.ReadOnlyField()
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)

    class Meta:
        model = Leave
        fields = [
            'id', 'employee', 'employee_name', 'leave_type', 'start_date',
            'end_date', 'days_count', 'reason', 'status', 'approved_by',
            'approved_by_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        """Valide les dates de congé et le solde disponible"""
        if data.get('start_date') and data.get('end_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError({
                    'end_date': "La date de fin doit être postérieure à la date de début."
                })

            # Calculer le nombre de jours demandés
            days_requested = (data['end_date'] - data['start_date']).days + 1

            # Vérifier le solde de congés (seulement pour les congés payés)
            employee = data.get('employee')
            if employee and data.get('leave_type') == 'paid':
                available_balance = employee.leave_balance
                pending_days = employee.leaves_pending_this_year

                # Le solde disponible moins les jours déjà en attente
                effective_balance = available_balance - pending_days

                if days_requested > effective_balance:
                    raise serializers.ValidationError({
                        'end_date': f"Solde de congés insuffisant. Vous avez {available_balance} jours disponibles "
                                   f"({pending_days} jours en attente d'approbation). "
                                   f"Vous demandez {days_requested} jours."
                    })

        return data


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle Attendance"""
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
        """Valide les heures de pointage"""
        if data.get('check_in') and data.get('check_out'):
            if data['check_out'] <= data['check_in']:
                raise serializers.ValidationError({
                    'check_out': "L'heure de sortie doit être postérieure à l'heure d'entrée."
                })
        return data


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer pour l'enregistrement d'utilisateurs"""
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    role = serializers.ChoiceField(choices=['admin', 'manager', 'employee'], required=False)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name', 'role']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        role = validated_data.pop('role', 'employee')

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            password=validated_data['password']
        )

        # Définir les permissions en fonction du rôle
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'manager':
            user.is_staff = True

        user.save()
        return user
