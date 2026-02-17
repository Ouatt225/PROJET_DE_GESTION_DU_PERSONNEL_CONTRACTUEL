from django.db import models
from django.contrib.auth.models import User


class Direction(models.Model):
    """Modèle pour les directions"""
    name = models.CharField(max_length=200, unique=True, verbose_name="Nom de la direction")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Direction"
        verbose_name_plural = "Directions"
        ordering = ['name']

    def __str__(self):
        return self.name


class ManagerProfile(models.Model):
    """Profil manager - lie un utilisateur à ses directions"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='manager_profile',
        verbose_name="Utilisateur"
    )
    directions = models.ManyToManyField(
        Direction,
        blank=True,
        related_name='managers',
        verbose_name="Directions gérées"
    )

    class Meta:
        verbose_name = "Profil Manager"
        verbose_name_plural = "Profils Manager"

    def __str__(self):
        dirs = ", ".join(d.name for d in self.directions.all())
        return f"{self.user.username} - {dirs or 'Aucune direction'}"


class CompanyProfile(models.Model):
    """Profil entreprise - lie un utilisateur à son entreprise"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='company_profile',
        verbose_name="Utilisateur"
    )
    department = models.ForeignKey(
        'Department',
        on_delete=models.CASCADE,
        related_name='company_managers',
        verbose_name="Entreprise"
    )

    class Meta:
        verbose_name = "Profil Entreprise"
        verbose_name_plural = "Profils Entreprise"

    def __str__(self):
        return f"{self.user.username} - {self.department.name}"


class Department(models.Model):
    """Modèle pour les entreprises"""
    name = models.CharField(max_length=200, verbose_name="Nom")
    manager = models.CharField(max_length=200, blank=True, null=True, verbose_name="Responsable")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Entreprise"
        verbose_name_plural = "Entreprises"
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def employees_count(self):
        return self.employees.count()


class Employee(models.Model):
    """Modèle pour les employés"""
    STATUS_CHOICES = [
        ('active', 'Actif'),
        ('inactive', 'Inactif'),
        ('on_leave', 'En congé'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('single', 'Célibataire'),
        ('married', 'Marié(e)'),
        ('divorced', 'Divorcé(e)'),
        ('widowed', 'Veuf/Veuve'),
    ]

    GENDER_CHOICES = [
        ('male', 'Masculin'),
        ('female', 'Féminin'),
    ]

    matricule = models.CharField(
        max_length=50,
        verbose_name="Matricule",
        null=True,
        blank=True,
        unique=True
    )
    first_name = models.CharField(max_length=100, verbose_name="Prénom")
    last_name = models.CharField(max_length=100, verbose_name="Nom")
    email = models.EmailField(unique=True, verbose_name="Email")
    phone = models.CharField(max_length=20, verbose_name="Téléphone", null=True, blank=True)
    birth_date = models.DateField(verbose_name="Date de naissance", null=True, blank=True)
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        verbose_name="Sexe",
        null=True,
        blank=True
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='employees',
        verbose_name="Entreprise"
    )
    direction = models.CharField(
        max_length=200,
        verbose_name="Direction",
        null=True,
        blank=True
    )
    position = models.CharField(max_length=100, verbose_name="Poste")
    hire_date = models.DateField(verbose_name="Date d'embauche")
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Salaire"
    )
    cnps = models.CharField(
        max_length=50,
        verbose_name="Numéro CNPS",
        null=True,
        blank=True
    )
    # Adresse détaillée
    city = models.CharField(max_length=100, verbose_name="Ville", null=True, blank=True)
    commune = models.CharField(max_length=100, blank=True, null=True, verbose_name="Commune")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse complète")
    # Situation familiale
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        verbose_name="Situation matrimoniale",
        null=True,
        blank=True
    )
    number_of_children = models.PositiveIntegerField(default=0, verbose_name="Nombre d'enfants")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name="Statut"
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profile',
        verbose_name="Utilisateur"
    )
    # Documents d'identité
    photo = models.ImageField(
        upload_to='employees/photos/',
        verbose_name="Photo d'identité",
        null=True,
        blank=True
    )
    cni_recto = models.FileField(
        upload_to='employees/cni/',
        verbose_name="CNI Recto",
        null=True,
        blank=True
    )
    cni_verso = models.FileField(
        upload_to='employees/cni/',
        verbose_name="CNI Verso",
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    # Quota annuel de congés (en jours)
    ANNUAL_LEAVE_ALLOWANCE = 30

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def leaves_taken_this_year(self):
        """Calcule le nombre de jours de congés pris (approuvés) cette année"""
        from datetime import date
        current_year = date.today().year
        approved_leaves = self.leaves.filter(
            status='approved',
            start_date__year=current_year
        )
        total_days = 0
        for leave in approved_leaves:
            total_days += (leave.end_date - leave.start_date).days + 1
        return total_days

    @property
    def leaves_pending_this_year(self):
        """Calcule le nombre de jours de congés en attente cette année"""
        from datetime import date
        current_year = date.today().year
        pending_leaves = self.leaves.filter(
            status='pending',
            start_date__year=current_year
        )
        total_days = 0
        for leave in pending_leaves:
            total_days += (leave.end_date - leave.start_date).days + 1
        return total_days

    @property
    def leave_balance(self):
        """Calcule le solde de congés restant"""
        return self.ANNUAL_LEAVE_ALLOWANCE - self.leaves_taken_this_year


class PasswordRecord(models.Model):
    """Stocke les mots de passe en référence pour consultation admin"""
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('manager', 'Manager'),
        ('entreprise', 'Entreprise'),
        ('employee', 'Employé'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='password_record',
        verbose_name="Utilisateur"
    )
    password_plain = models.CharField(max_length=200, verbose_name="Mot de passe")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee', verbose_name="Rôle")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mot de passe"
        verbose_name_plural = "Mots de passe"
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"


class Leave(models.Model):
    """Modèle pour les demandes de congés"""
    LEAVE_TYPES = [
        ('paid', 'Congé Payé'),
        ('sick', 'Congé Maladie'),
        ('unpaid', 'Congé Sans Solde'),
        ('parental', 'Congé Parental'),
        ('other', 'Autre'),
    ]

    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('manager_approved', 'Validé Manager'),
        ('approved', 'Approuvé'),
        ('rejected', 'Rejeté'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='leaves',
        verbose_name="Employé"
    )
    leave_type = models.CharField(
        max_length=20,
        choices=LEAVE_TYPES,
        verbose_name="Type de congé"
    )
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    reason = models.TextField(blank=True, null=True, verbose_name="Raison")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Statut"
    )
    manager_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manager_approved_leaves',
        verbose_name="Validé par (Manager)"
    )
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves',
        verbose_name="Approuvé par (Entreprise)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Congé"
        verbose_name_plural = "Congés"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_leave_type_display()}"

    @property
    def days_count(self):
        """Calcule le nombre de jours de congé"""
        return (self.end_date - self.start_date).days + 1


class Attendance(models.Model):
    """Modèle pour la gestion des présences"""
    STATUS_CHOICES = [
        ('present', 'Présent'),
        ('absent', 'Absent'),
        ('late', 'En Retard'),
        ('half-day', 'Demi-journée'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name="Employé"
    )
    date = models.DateField(verbose_name="Date")
    check_in = models.TimeField(verbose_name="Heure d'arrivée", null=True, blank=True)
    check_out = models.TimeField(verbose_name="Heure de départ", null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='present',
        verbose_name="Statut"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Présence"
        verbose_name_plural = "Présences"
        ordering = ['-date']
        unique_together = ['employee', 'date']

    def __str__(self):
        return f"{self.employee.full_name} - {self.date}"

    @property
    def hours_worked(self):
        """Calcule les heures travaillées"""
        if self.check_in and self.check_out:
            from datetime import datetime, timedelta
            check_in_time = datetime.combine(datetime.today(), self.check_in)
            check_out_time = datetime.combine(datetime.today(), self.check_out)
            delta = check_out_time - check_in_time
            return round(delta.total_seconds() / 3600, 2)
        return 0
