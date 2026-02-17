from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from .models import Direction, ManagerProfile, CompanyProfile, Department, Employee, Leave, Attendance, PasswordRecord


# ===========================
# Admin Direction
# ===========================
@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'get_managers', 'created_at']
    search_fields = ['name']
    ordering = ['name']

    def get_managers(self, obj):
        managers = obj.managers.all()
        if managers:
            return ", ".join(mp.user.username for mp in managers)
        return "-"
    get_managers.short_description = "Managers assignés"


# ===========================
# Inline pour les directions du manager
# ===========================
class ManagerProfileInline(admin.StackedInline):
    model = ManagerProfile
    can_delete = False
    verbose_name = "Directions gérées"
    verbose_name_plural = "Directions gérées"
    filter_horizontal = ('directions',)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        return formset


# ===========================
# Formulaire personnalisé pour la création d'utilisateurs
# ===========================
class CustomUserCreationForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('employee', 'Employé'),
        ('manager', 'Manager'),
        ('entreprise', 'Entreprise'),
        ('admin', 'Administrateur'),
    ]

    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput)
    role = forms.ChoiceField(
        label='Rôle',
        choices=ROLE_CHOICES,
        initial='employee',
        help_text='Employé: accès contractuel | Manager: accès par directions | Entreprise: accès à son entreprise | Admin: accès complet'
    )
    directions = forms.ModelMultipleChoiceField(
        queryset=Direction.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Directions à gérer',
        help_text='Pour le rôle Manager uniquement.'
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='Entreprise',
        help_text='Pour le rôle Entreprise uniquement.'
    )

    class Meta:
        model = User
        fields = ('username',)

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Les mots de passe ne correspondent pas')
        return password2

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'entreprise' and not cleaned_data.get('department'):
            raise forms.ValidationError('Vous devez sélectionner une entreprise pour le rôle Entreprise.')
        if role == 'manager' and not cleaned_data.get('directions'):
            raise forms.ValidationError('Vous devez sélectionner au moins une direction pour le rôle Manager.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password_plain = self.cleaned_data['password1']
        user.set_password(password_plain)

        role = self.cleaned_data.get('role')
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role in ('manager', 'entreprise'):
            user.is_staff = True
            user.is_superuser = False
        else:
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()

            if role == 'manager':
                profile, _ = ManagerProfile.objects.get_or_create(user=user)
                directions = self.cleaned_data.get('directions')
                if directions:
                    profile.directions.set(directions)

            if role == 'entreprise':
                department = self.cleaned_data.get('department')
                CompanyProfile.objects.update_or_create(
                    user=user,
                    defaults={'department': department}
                )

            PasswordRecord.objects.update_or_create(
                user=user,
                defaults={
                    'password_plain': password_plain,
                    'role': role,
                }
            )

        return user


# ===========================
# Formulaire personnalisé pour la modification d'utilisateurs
# ===========================
class CustomUserChangeForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('employee', 'Employé'),
        ('manager', 'Manager'),
        ('entreprise', 'Entreprise'),
        ('admin', 'Administrateur'),
    ]

    role = forms.ChoiceField(label='Rôle', choices=ROLE_CHOICES)
    directions = forms.ModelMultipleChoiceField(
        queryset=Direction.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label='Directions à gérer',
        help_text='Pour le rôle Manager uniquement.'
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='Entreprise',
        help_text='Pour le rôle Entreprise uniquement.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.is_superuser:
                self.fields['role'].initial = 'admin'
            else:
                try:
                    self.instance.company_profile
                    self.fields['role'].initial = 'entreprise'
                    self.fields['department'].initial = self.instance.company_profile.department
                except CompanyProfile.DoesNotExist:
                    if self.instance.is_staff:
                        self.fields['role'].initial = 'manager'
                    else:
                        self.fields['role'].initial = 'employee'

            try:
                profile = self.instance.manager_profile
                self.fields['directions'].initial = profile.directions.all()
            except ManagerProfile.DoesNotExist:
                pass

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'entreprise' and not cleaned_data.get('department'):
            raise forms.ValidationError('Vous devez sélectionner une entreprise pour le rôle Entreprise.')
        if role == 'manager' and not cleaned_data.get('directions'):
            raise forms.ValidationError('Vous devez sélectionner au moins une direction pour le rôle Manager.')
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        role = self.cleaned_data.get('role')
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role in ('manager', 'entreprise'):
            user.is_staff = True
            user.is_superuser = False
        else:
            user.is_staff = False
            user.is_superuser = False

        if commit:
            user.save()

            if role == 'manager':
                profile, _ = ManagerProfile.objects.get_or_create(user=user)
                directions = self.cleaned_data.get('directions')
                if directions is not None:
                    profile.directions.set(directions)
            else:
                ManagerProfile.objects.filter(user=user).delete()

            if role == 'entreprise':
                department = self.cleaned_data.get('department')
                CompanyProfile.objects.update_or_create(
                    user=user,
                    defaults={'department': department}
                )
            else:
                CompanyProfile.objects.filter(user=user).delete()

        return user


# ===========================
# Admin personnalisé pour les utilisateurs
# ===========================
admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm

    list_display = ['username', 'email', 'first_name', 'last_name', 'get_role', 'get_directions', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'role', 'directions', 'department'),
            'description': 'Créez un compte. Manager = directions, Entreprise = entreprise.',
        }),
    )

    fieldsets = (
        ('Informations de connexion', {
            'fields': ('username', 'email')
        }),
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name')
        }),
        ('Rôle et permissions', {
            'fields': ('role', 'is_active')
        }),
        ('Directions gérées (Manager)', {
            'fields': ('directions',),
        }),
        ('Entreprise gérée (Entreprise)', {
            'fields': ('department',),
        }),
    )

    def save_model(self, request, obj, form, change):
        """Sauvegarde le user et crée automatiquement le ManagerProfile si rôle = manager"""
        super().save_model(request, obj, form, change)
        role = form.cleaned_data.get('role')
        if role == 'manager':
            profile, _ = ManagerProfile.objects.get_or_create(user=obj)
            directions = form.cleaned_data.get('directions')
            if directions:
                profile.directions.set(directions)
        elif role != 'manager':
            ManagerProfile.objects.filter(user=obj).delete()
        if role == 'entreprise':
            department = form.cleaned_data.get('department')
            if department:
                CompanyProfile.objects.update_or_create(
                    user=obj,
                    defaults={'department': department}
                )
        elif role != 'entreprise':
            CompanyProfile.objects.filter(user=obj).delete()

    def get_role(self, obj):
        if obj.is_superuser:
            return 'Administrateur'
        try:
            obj.company_profile
            return 'Entreprise'
        except CompanyProfile.DoesNotExist:
            pass
        if obj.is_staff:
            return 'Manager'
        return 'Employé'
    get_role.short_description = 'Rôle'

    def get_directions(self, obj):
        try:
            profile = obj.company_profile
            return f"[Entreprise] {profile.department.name}"
        except CompanyProfile.DoesNotExist:
            pass
        try:
            profile = obj.manager_profile
            dirs = profile.directions.all()
            if dirs:
                return ", ".join(d.name for d in dirs)
        except ManagerProfile.DoesNotExist:
            pass
        return "-"
    get_directions.short_description = 'Directions / Entreprise'

    class Media:
        js = ('admin/js/manager_directions.js',)


# ===========================
# Admin ManagerProfile (standalone)
# ===========================
@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_role_display', 'get_directions']
    filter_horizontal = ('directions',)
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    def get_role_display(self, obj):
        return 'Manager'
    get_role_display.short_description = 'Rôle'

    def get_directions(self, obj):
        dirs = obj.directions.all()
        if dirs:
            return ", ".join(d.name for d in dirs)
        return "-"
    get_directions.short_description = 'Directions gérées'


# ===========================
# Admin CompanyProfile
# ===========================
@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department', 'get_employees_count']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'department__name']
    list_filter = ['department']

    def get_employees_count(self, obj):
        return obj.department.employees.count()
    get_employees_count.short_description = "Nombre d'employés"


# ===========================
# Admin Department
# ===========================
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'employees_count', 'created_at']
    search_fields = ['name', 'manager']
    list_filter = ['created_at']
    ordering = ['name']


# ===========================
# Admin Employee
# ===========================
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'department', 'direction', 'position', 'status', 'hire_date']
    search_fields = ['first_name', 'last_name', 'email', 'cnps', 'direction']
    list_filter = ['status', 'department', 'direction', 'hire_date']
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address')
        }),
        ('Informations professionnelles', {
            'fields': ('department', 'direction', 'position', 'hire_date', 'salary', 'matricule', 'cnps', 'status')
        }),
        ('Compte utilisateur', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
    )


# ===========================
# Admin Leave
# ===========================
@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'days_count', 'status', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    list_filter = ['status', 'leave_type', 'start_date']
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Employé', {
            'fields': ('employee',)
        }),
        ('Détails du congé', {
            'fields': ('leave_type', 'start_date', 'end_date', 'reason')
        }),
        ('Approbation', {
            'fields': ('status', 'manager_approved_by', 'approved_by')
        }),
    )


# ===========================
# Admin Attendance
# ===========================
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'hours_worked', 'status']
    search_fields = ['employee__first_name', 'employee__last_name']
    list_filter = ['status', 'date']
    ordering = ['-date']
    list_per_page = 25

    fieldsets = (
        ('Employé', {
            'fields': ('employee', 'date')
        }),
        ('Pointage', {
            'fields': ('check_in', 'check_out', 'status')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )


# ===========================
# Admin PasswordRecord
# ===========================
@admin.register(PasswordRecord)
class PasswordRecordAdmin(admin.ModelAdmin):
    list_display = ['get_full_name', 'get_username', 'password_plain', 'role', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    list_filter = ['role']
    ordering = ['user__last_name', 'user__first_name']
    list_per_page = 50

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Nom complet'

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Identifiant'
