"""
Configuration de l'interface d'administration Django pour le système de gestion
du personnel contractuel DAF-MEER.

Ce module personnalise entièrement l'interface Django Admin pour :

  Gestion des utilisateurs :
    CustomUserCreationForm  — Formulaire de création avec sélection du rôle et
                              des directions / entreprise associées.
    CustomUserChangeForm    — Formulaire de modification avec détection automatique
                              du rôle courant et mise à jour des profils associés.
    CustomUserAdmin         — Remplacement du UserAdmin Django standard, incluant
                              l'affichage du rôle et des périmètres gérés.

  Administration des modèles métier :
    DirectionAdmin          — Directions avec liste des managers assignés.
    ManagerProfileAdmin     — Profils managers avec directions associées.
    CompanyProfileAdmin     — Profils entreprise avec compteur d'employés.
    DepartmentAdmin         — Entreprises prestataires.
    EmployeeAdmin           — Agents contractuels avec fieldsets thématiques.
    LeaveAdmin              — Demandes de congé avec fieldsets d'approbation.
    AttendanceAdmin         — Pointages de présence.
    PasswordRecordAdmin     — Mots de passe chiffrés (masqués dans la liste,
                              déchiffrables via get_decrypted_password).

Sécurité :
    - Les mots de passe sont chiffrés via Fernet avant stockage dans PasswordRecord.
    - L'interface Admin ne montre jamais le mot de passe en clair dans la liste.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from .models import Direction, ManagerProfile, CompanyProfile, Department, Employee, Leave, Attendance, PasswordRecord
from .encryption import encrypt_password, decrypt_password


# ===========================
# Admin Direction
# ===========================

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    """Administration des directions ministérielles.

    Affiche la liste des managers assignés à chaque direction dans la vue liste.
    """

    list_display = ['name', 'get_managers', 'created_at']
    search_fields = ['name']
    ordering = ['name']

    def get_managers(self, obj):
        """Retourne une chaîne des usernames des managers de cette direction.

        Args:
            obj (Direction): Instance de la direction.

        Returns:
            str: Noms des managers séparés par des virgules, ou '-' si aucun.
        """
        managers = obj.managers.all()
        if managers:
            return ", ".join(mp.user.username for mp in managers)
        return "-"
    get_managers.short_description = "Managers assignés"


# ===========================
# Inline pour les directions du manager
# ===========================

class ManagerProfileInline(admin.StackedInline):
    """Inline permettant de gérer les directions d'un manager depuis la fiche User.

    Affiché dans CustomUserAdmin pour les utilisateurs de type 'manager'.
    """

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
    """Formulaire de création d'un utilisateur avec gestion du rôle.

    Étend le formulaire Django standard avec :
      - Champ `role` : détermine les permissions Django (is_staff, is_superuser)
        et crée automatiquement le profil associé (ManagerProfile ou CompanyProfile).
      - Champ `directions` : sélection multiple des directions (rôle Manager).
      - Champ `department` : sélection de l'entreprise (rôle Entreprise).
      - Champs `password1` / `password2` : saisie et confirmation du mot de passe.

    À la sauvegarde, crée également un PasswordRecord chiffré (Fernet).
    """

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
        """Vérifie que les deux mots de passe saisis correspondent.

        Returns:
            str: Le mot de passe confirmé.

        Raises:
            forms.ValidationError: Si password1 != password2.
        """
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Les mots de passe ne correspondent pas')
        return password2

    def clean(self):
        """Validation croisée : vérifie les champs obligatoires selon le rôle.

        Returns:
            dict: Données nettoyées.

        Raises:
            forms.ValidationError: Si le rôle 'entreprise' est sélectionné sans entreprise,
                ou si le rôle 'manager' est sélectionné sans direction.
        """
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'entreprise' and not cleaned_data.get('department'):
            raise forms.ValidationError('Vous devez sélectionner une entreprise pour le rôle Entreprise.')
        if role == 'manager' and not cleaned_data.get('directions'):
            raise forms.ValidationError('Vous devez sélectionner au moins une direction pour le rôle Manager.')
        return cleaned_data

    def save(self, commit=True):
        """Sauvegarde l'utilisateur, configure ses permissions et crée les profils associés.

        Actions effectuées :
          1. Hash du mot de passe via User.set_password().
          2. Définition des flags Django (is_staff, is_superuser) selon le rôle.
          3. Création de ManagerProfile avec les directions sélectionnées.
          4. Création de CompanyProfile avec l'entreprise sélectionnée.
          5. Création de PasswordRecord avec le mot de passe chiffré (Fernet).

        Args:
            commit (bool): Si True, sauvegarde en base de données.

        Returns:
            User: Instance de l'utilisateur créé.
        """
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

            # Stocker le mot de passe chiffré pour consultation admin ultérieure
            PasswordRecord.objects.update_or_create(
                user=user,
                defaults={
                    'password_encrypted': encrypt_password(password_plain),
                    'role': role,
                }
            )

        return user


# ===========================
# Formulaire personnalisé pour la modification d'utilisateurs
# ===========================

class CustomUserChangeForm(forms.ModelForm):
    """Formulaire de modification d'un utilisateur existant avec gestion du rôle.

    Pré-remplit automatiquement le rôle détecté en lisant les champs Django
    (is_superuser, is_staff) et les profils personnalisés (CompanyProfile, ManagerProfile).

    Permet de changer le rôle d'un utilisateur, ce qui met à jour ou supprime
    les profils ManagerProfile et CompanyProfile en conséquence.

    Note : ce formulaire ne gère pas le changement de mot de passe
    (utiliser ChangePasswordView ou l'interface Django dédiée).
    """

    ROLE_CHOICES = [
        ('employee', 'Employé'),
        ('manager', 'Manager'),
        ('entreprise', 'Entreprise'),
        ('admin', 'Administrateur'),
    ]

    password = ReadOnlyPasswordHashField(
        label='Mot de passe',
        help_text='Les mots de passe bruts ne sont pas enregistrés. '
                  'Vous pouvez modifier le mot de passe en utilisant '
                  '<a href="../password/">ce formulaire</a>.'
    )

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
        fields = ('username', 'password', 'email', 'first_name', 'last_name', 'is_active')

    def __init__(self, *args, **kwargs):
        """Initialise le formulaire et détecte le rôle courant de l'utilisateur.

        Pré-remplit les champs 'role', 'department' et 'directions' en lisant :
          - is_superuser → 'admin'
          - CompanyProfile existant → 'entreprise'
          - is_staff → 'manager'
          - Sinon → 'employee'
        """
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
        """Validation croisée : vérifie les champs obligatoires selon le rôle.

        Returns:
            dict: Données nettoyées.

        Raises:
            forms.ValidationError: Si le rôle impose des champs manquants.
        """
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        if role == 'entreprise' and not cleaned_data.get('department'):
            raise forms.ValidationError('Vous devez sélectionner une entreprise pour le rôle Entreprise.')
        if role == 'manager' and not cleaned_data.get('directions'):
            raise forms.ValidationError('Vous devez sélectionner au moins une direction pour le rôle Manager.')
        return cleaned_data

    def save(self, commit=True):
        """Sauvegarde les modifications et met à jour les profils associés.

        Met à jour les flags Django, puis crée/supprime les profils ManagerProfile
        et CompanyProfile selon le nouveau rôle choisi.

        Args:
            commit (bool): Si True, sauvegarde en base de données.

        Returns:
            User: Instance de l'utilisateur modifié.
        """
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
                # Supprimer le profil manager si le rôle a changé
                ManagerProfile.objects.filter(user=user).delete()

            if role == 'entreprise':
                department = self.cleaned_data.get('department')
                CompanyProfile.objects.update_or_create(
                    user=user,
                    defaults={'department': department}
                )
            else:
                # Supprimer le profil entreprise si le rôle a changé
                CompanyProfile.objects.filter(user=user).delete()

        return user


# ===========================
# Admin personnalisé pour les utilisateurs
# ===========================

admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    """Remplacement du UserAdmin Django standard avec gestion des rôles métier.

    Remplace les formulaires de création et modification Django standard par
    CustomUserCreationForm et CustomUserChangeForm.

    Colonnes supplémentaires dans la liste :
      - Rôle (admin, manager, entreprise, employé)
      - Directions gérées ou entreprise associée

    Fichier JavaScript inclus (admin/js/manager_directions.js) pour masquer/afficher
    dynamiquement les champs directions et department selon le rôle sélectionné.
    """

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
            'fields': ('username', 'password', 'email')
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
        """Sauvegarde le User et synchronise les profils ManagerProfile / CompanyProfile.

        Appelé par Django Admin après validation du formulaire.
        Crée ou supprime les profils selon le nouveau rôle.

        Args:
            request (HttpRequest): Requête HTTP.
            obj (User): Instance de l'utilisateur à sauvegarder.
            form (ModelForm): Formulaire validé.
            change (bool): True si modification, False si création.
        """
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
        """Retourne le libellé du rôle de l'utilisateur pour la colonne de liste.

        Détecte le rôle en inspectant is_superuser, CompanyProfile et is_staff.

        Args:
            obj (User): Instance de l'utilisateur.

        Returns:
            str: 'Administrateur' | 'Entreprise' | 'Manager' | 'Employé'.
        """
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
        """Retourne les directions gérées ou l'entreprise associée à l'utilisateur.

        Args:
            obj (User): Instance de l'utilisateur.

        Returns:
            str: '[Entreprise] <nom>' pour les entreprises, liste de directions
                 pour les managers, ou '-'.
        """
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
        # Script JS pour l'affichage conditionnel des champs selon le rôle sélectionné
        js = ('admin/js/manager_directions.js',)


# ===========================
# Admin ManagerProfile (standalone)
# ===========================

@admin.register(ManagerProfile)
class ManagerProfileAdmin(admin.ModelAdmin):
    """Administration autonome des profils manager.

    Permet de consulter et modifier directement les directions assignées
    à chaque manager, indépendamment de la fiche User.
    """

    list_display = ['user', 'get_role_display', 'get_directions']
    filter_horizontal = ('directions',)
    search_fields = ['user__username', 'user__first_name', 'user__last_name']

    def get_role_display(self, obj):
        """Retourne le libellé du rôle (toujours 'Manager' pour ce modèle).

        Args:
            obj (ManagerProfile): Instance du profil manager.

        Returns:
            str: 'Manager'.
        """
        return 'Manager'
    get_role_display.short_description = 'Rôle'

    def get_directions(self, obj):
        """Retourne la liste des noms de directions gérées par ce manager.

        Args:
            obj (ManagerProfile): Instance du profil manager.

        Returns:
            str: Noms de directions séparés par des virgules, ou '-'.
        """
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
    """Administration des profils entreprise.

    Affiche le nombre d'employés rattachés à l'entreprise de chaque profil.
    """

    list_display = ['user', 'department', 'get_employees_count']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'department__name']
    list_filter = ['department']

    def get_employees_count(self, obj):
        """Retourne le nombre d'employés rattachés à l'entreprise du profil.

        Args:
            obj (CompanyProfile): Instance du profil entreprise.

        Returns:
            int: Nombre d'employés dans l'entreprise associée.
        """
        return obj.department.employees.count()
    get_employees_count.short_description = "Nombre d'employés"


# ===========================
# Admin Department
# ===========================

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Administration des entreprises prestataires."""

    list_display = ['name', 'manager', 'employees_count', 'created_at']
    search_fields = ['name', 'manager']
    list_filter = ['created_at']
    ordering = ['name']


# ===========================
# Admin Employee
# ===========================

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Administration des agents contractuels avec fieldsets thématiques.

    Les champs sont regroupés par thème : informations personnelles,
    informations professionnelles et compte utilisateur (réduit par défaut).
    """

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
    """Administration des demandes de congé avec fieldsets d'approbation.

    Le fieldset 'Approbation' regroupe le statut et les deux validateurs
    (manager de direction, puis entreprise).
    """

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
    """Administration des enregistrements de présence (pointages).

    Les notes sont accessibles dans un fieldset réduit (collapse).
    """

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
    """Administration des mots de passe chiffrés.

    Le mot de passe est masqué dans la colonne de liste (affichage '••••••••').
    La méthode get_decrypted_password est disponible pour les actions admin
    ou les fieldsets personnalisés, mais n'est pas exposée dans la liste
    par défaut pour des raisons de sécurité.
    """

    list_display = ['get_full_name', 'get_username', 'get_masked_password', 'role', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name']
    list_filter = ['role']
    ordering = ['user__last_name', 'user__first_name']
    list_per_page = 50

    def get_full_name(self, obj):
        """Retourne le nom complet de l'utilisateur ou son username.

        Args:
            obj (PasswordRecord): Instance du mot de passe.

        Returns:
            str: Nom complet ou username.
        """
        return obj.user.get_full_name() or obj.user.username
    get_full_name.short_description = 'Nom complet'

    def get_username(self, obj):
        """Retourne l'identifiant de connexion de l'utilisateur.

        Args:
            obj (PasswordRecord): Instance du mot de passe.

        Returns:
            str: Username Django.
        """
        return obj.user.username
    get_username.short_description = 'Identifiant'

    def get_masked_password(self, obj):
        """Retourne le mot de passe masqué pour l'affichage dans la liste.

        Le mot de passe n'est jamais affiché en clair dans la liste
        pour des raisons de sécurité.

        Args:
            obj (PasswordRecord): Instance du mot de passe.

        Returns:
            str: Chaîne de points '••••••••'.
        """
        return '••••••••'
    get_masked_password.short_description = 'Mot de passe'

    def get_decrypted_password(self, obj):
        """Retourne le mot de passe déchiffré (pour usage dans fieldsets ou actions admin).

        Appelle PasswordRecord.get_password() qui utilise Fernet pour déchiffrer.
        Ne pas exposer dans list_display en production.

        Args:
            obj (PasswordRecord): Instance du mot de passe.

        Returns:
            str: Mot de passe en clair, ou '(indéchiffrable)' si le token Fernet est invalide.
        """
        return obj.get_password()
    get_decrypted_password.short_description = 'Mot de passe (visible)'
