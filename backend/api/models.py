"""
Modèles de données de l'application de gestion du personnel contractuel.

Hiérarchie des modèles :
  Direction       — Direction ministérielle (ex. DAF, MEER)
  ManagerProfile  — Lie un User Django à une ou plusieurs Direction(s)
  CompanyProfile  — Lie un User Django à un Department (entreprise prestataire)
  Department      — Entreprise prestataire (ex. AZING, CAFOR)
  Employee        — Agent contractuel, rattaché à un Department et une Direction
  Leave           — Demande de congé d'un Employee
  Attendance      — Enregistrement de présence journalier d'un Employee
  PasswordRecord  — Mot de passe chiffré (Fernet) pour consultation admin

Flux d'approbation des congés :
  Employee soumet → pending
  Manager valide  → manager_approved
  Entreprise approuve → approved  (ou rejected à n'importe quelle étape)
"""

from django.db import models
from django.contrib.auth.models import User


class Direction(models.Model):
    """Direction ministérielle gérant un ensemble d'employés contractuels.

    Une Direction regroupe des agents selon leur rattachement administratif
    (ex. « Direction des Affaires Financières »). Elle est associée à un ou
    plusieurs managers via ManagerProfile.

    Attributes:
        name (CharField): Nom unique de la direction (max. 200 caractères).
        created_at (DateTimeField): Date de création (auto).
    """

    name = models.CharField(max_length=200, unique=True, verbose_name="Nom de la direction")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Direction"
        verbose_name_plural = "Directions"
        ordering = ['name']

    def __str__(self):
        return self.name


class ManagerProfile(models.Model):
    """Profil manager : lie un utilisateur Django aux directions qu'il supervise.

    Un manager peut être responsable de plusieurs directions simultanément.
    Ce profil est créé automatiquement par CustomUserAdmin lors de la
    création d'un utilisateur avec le rôle 'manager'.

    Attributes:
        user (OneToOneField → User): Utilisateur Django associé.
        directions (ManyToManyField → Direction): Directions supervisées.
    """

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
    """Profil entreprise : lie un utilisateur Django à l'entreprise qu'il gère.

    Un utilisateur de type 'entreprise' ne voit que les employés affiliés
    à son entreprise (Department). Ce profil est créé automatiquement par
    CustomUserAdmin lors de l'attribution du rôle 'entreprise'.

    Attributes:
        user (OneToOneField → User): Utilisateur Django associé.
        department (ForeignKey → Department): Entreprise gérée par cet utilisateur.
    """

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
    """Entreprise prestataire regroupant des agents contractuels.

    Dans ce système, "Department" désigne une entreprise externe fournissant
    des agents contractuels (ex. AZING, CAFOR, IVOIR GARDIENNAGE).
    Chaque Department peut avoir un ou plusieurs CompanyProfile associés.

    Attributes:
        name (CharField): Nom de l'entreprise.
        manager (CharField): Nom du responsable de l'entreprise (texte libre).
        description (TextField): Description ou informations complémentaires.
        created_at (DateTimeField): Date de création (auto).
        updated_at (DateTimeField): Date de dernière modification (auto).

    Properties:
        employees_count (int): Nombre d'employés actifs dans cette entreprise.
    """

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
        """Retourne le nombre d'employés rattachés à cette entreprise.

        Returns:
            int: Nombre d'instances Employee ayant ce Department comme FK.
        """
        return self.employees.count()


class Employee(models.Model):
    """Agent contractuel géré par le système.

    Un employé est rattaché à une entreprise prestataire (Department)
    et à une direction ministérielle (direction, champ texte libre).
    Il peut avoir un compte utilisateur Django (user) pour accéder à
    son espace personnel (employee-profile.html).

    Attributes:
        matricule (CharField): Numéro matricule unique (nullable).
        first_name (CharField): Prénom de l'agent.
        last_name (CharField): Nom de famille de l'agent.
        email (EmailField): Adresse e-mail unique.
        phone (CharField): Numéro de téléphone (nullable).
        birth_date (DateField): Date de naissance (nullable).
        gender (CharField): Sexe ('male' | 'female', nullable).
        department (ForeignKey → Department): Entreprise prestataire.
        direction (CharField): Direction ministérielle (texte libre, nullable).
        position (CharField): Poste ou fonction occupée.
        hire_date (DateField): Date de prise de fonction.
        salary (DecimalField): Salaire mensuel brut.
        cnps (CharField): Numéro d'immatriculation CNPS (nullable).
        city (CharField): Ville de résidence (nullable).
        commune (CharField): Commune de résidence (nullable).
        address (TextField): Adresse complète (nullable).
        marital_status (CharField): Situation matrimoniale (nullable).
        number_of_children (PositiveIntegerField): Nombre d'enfants à charge.
        status (CharField): Statut contractuel ('active' | 'inactive' | 'on_leave').
        user (OneToOneField → User): Compte utilisateur Django associé (nullable).
        photo (ImageField): Photo d'identité (nullable).
        cni_recto (FileField): Scan recto de la CNI (nullable).
        cni_verso (FileField): Scan verso de la CNI (nullable).
        created_at (DateTimeField): Date de création (auto).
        updated_at (DateTimeField): Date de dernière modification (auto).

    Class attributes:
        ANNUAL_LEAVE_ALLOWANCE (int): Quota annuel de congés payés = 30 jours.

    Properties:
        full_name (str): Prénom + Nom.
        leaves_taken_this_year (int): Jours de congés payés approuvés cette année.
        leaves_pending_this_year (int): Jours de congés payés en attente cette année.
        leave_balance (int): Solde de congés payés restant.
    """

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

    # Quota annuel de congés payés (en jours)
    ANNUAL_LEAVE_ALLOWANCE = 30

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

    @property
    def full_name(self):
        """Retourne le nom complet de l'employé (prénom + nom).

        Returns:
            str: Chaîne « Prénom Nom ».
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def leaves_taken_this_year(self):
        """Calcule les jours de congés payés approuvés cette année civile.

        Seuls les congés de type 'paid' comptent contre le quota annuel.
        Les congés maladie, sans solde et parental n'affectent pas ce solde.

        Returns:
            int: Nombre total de jours de congés payés approuvés en cours d'année.
        """
        from datetime import date
        current_year = date.today().year
        approved_leaves = self.leaves.filter(
            leave_type='paid',
            status='approved',
            start_date__year=current_year
        )
        total_days = 0
        for leave in approved_leaves:
            total_days += (leave.end_date - leave.start_date).days + 1
        return total_days

    @property
    def leaves_pending_this_year(self):
        """Calcule les jours de congés payés en attente cette année civile.

        Inclut les statuts 'pending' et 'manager_approved'.
        Utilisé pour calculer le solde effectif disponible avant d'approuver
        une nouvelle demande (leave_balance - leaves_pending).

        Returns:
            int: Nombre de jours de congés payés non encore approuvés cette année.
        """
        from datetime import date
        current_year = date.today().year
        pending_leaves = self.leaves.filter(
            leave_type='paid',
            status__in=['pending', 'manager_approved'],
            start_date__year=current_year
        )
        total_days = 0
        for leave in pending_leaves:
            total_days += (leave.end_date - leave.start_date).days + 1
        return total_days

    @property
    def leave_balance(self):
        """Calcule le solde de congés payés restants pour l'année en cours.

        Formule : ANNUAL_LEAVE_ALLOWANCE - leaves_taken_this_year

        Returns:
            int: Nombre de jours de congés payés encore disponibles.
        """
        return self.ANNUAL_LEAVE_ALLOWANCE - self.leaves_taken_this_year


class PasswordRecord(models.Model):
    """Stocke les mots de passe chiffrés (Fernet) pour consultation par les admins.

    Ce modèle permet aux administrateurs de retrouver et distribuer les
    identifiants des agents contractuels (export Excel).
    Le mot de passe est stocké chiffré avec l'algorithme Fernet (symétrique).
    La clé de chiffrement est lue depuis la variable d'environnement ENCRYPTION_KEY.

    IMPORTANT : Ne jamais changer ENCRYPTION_KEY en production — tous les
    mots de passe existants deviendraient illisibles.

    Attributes:
        user (OneToOneField → User): Utilisateur propriétaire du mot de passe.
        password_encrypted (CharField): Mot de passe chiffré en Base64 Fernet.
        role (CharField): Rôle de l'utilisateur ('admin'|'manager'|'entreprise'|'employee').
        created_at (DateTimeField): Date de création (auto).
        updated_at (DateTimeField): Date de dernière modification (auto).
    """

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
    password_encrypted = models.CharField(
        max_length=500,
        verbose_name="Mot de passe (chiffré)"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee', verbose_name="Rôle")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Mot de passe"
        verbose_name_plural = "Mots de passe"
        ordering = ['user__last_name', 'user__first_name']

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"

    def get_password(self) -> str:
        """Retourne le mot de passe déchiffré en clair.

        Appelle decrypt_password() du module encryption.
        Retourne '(indéchiffrable)' si la valeur stockée n'est pas
        un token Fernet valide.

        Returns:
            str: Mot de passe en clair, ou '(indéchiffrable)' en cas d'erreur.
        """
        from .encryption import decrypt_password
        return decrypt_password(self.password_encrypted)

    def set_password(self, plain_text: str) -> None:
        """Chiffre et stocke le mot de passe en clair.

        Appelle encrypt_password() du module encryption.
        Ne sauvegarde PAS l'instance en base de données — appeler .save()
        ou update_or_create() séparément.

        Args:
            plain_text (str): Mot de passe en clair à chiffrer et stocker.

        Returns:
            None
        """
        from .encryption import encrypt_password
        self.password_encrypted = encrypt_password(plain_text)


class Leave(models.Model):
    """Demande de congé d'un employé.

    Flux de statuts :
        pending → manager_approved → approved
        pending | manager_approved → rejected

    Seuls les congés de type 'paid' sont décomptés du quota annuel
    de l'employé (ANNUAL_LEAVE_ALLOWANCE = 30 jours).

    Attributes:
        employee (ForeignKey → Employee): Employé demandeur.
        leave_type (CharField): Type de congé ('paid'|'sick'|'unpaid'|'parental'|'other').
        start_date (DateField): Date de début du congé.
        end_date (DateField): Date de fin du congé (incluse).
        reason (TextField): Motif de la demande (nullable).
        status (CharField): Statut courant ('pending'|'manager_approved'|'approved'|'rejected').
        manager_approved_by (ForeignKey → User): Manager ayant effectué la première validation.
        approved_by (ForeignKey → User): Utilisateur ayant effectué l'approbation finale.
        created_at (DateTimeField): Date de création (auto).
        updated_at (DateTimeField): Date de dernière modification (auto).

    Properties:
        days_count (int): Nombre de jours calendaires du congé (bornes incluses).
    """

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
        """Calcule le nombre de jours calendaires du congé (bornes incluses).

        Returns:
            int: (end_date - start_date).days + 1
        """
        return (self.end_date - self.start_date).days + 1


class Attendance(models.Model):
    """Enregistrement de présence journalier d'un employé.

    Un seul enregistrement par (employee, date) est autorisé (unique_together).
    L'heure d'arrivée et de départ sont optionnelles (cas d'un statut 'absent').

    Attributes:
        employee (ForeignKey → Employee): Employé concerné.
        date (DateField): Date du pointage.
        check_in (TimeField): Heure d'arrivée (nullable).
        check_out (TimeField): Heure de départ (nullable).
        status (CharField): Statut ('present'|'absent'|'late'|'half-day').
        notes (TextField): Remarques libres (nullable).
        created_at (DateTimeField): Date de création (auto).
        updated_at (DateTimeField): Date de dernière modification (auto).

    Properties:
        hours_worked (float): Heures travaillées calculées depuis check_in/check_out.
    """

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
        """Calcule les heures travaillées à partir des heures de pointage.

        Si l'une des deux heures (check_in ou check_out) est absente,
        retourne 0.

        Returns:
            float: Nombre d'heures travaillées arrondi à 2 décimales,
                   ou 0 si le calcul est impossible.
        """
        if self.check_in and self.check_out:
            from datetime import datetime, timedelta
            check_in_time = datetime.combine(datetime.today(), self.check_in)
            check_out_time = datetime.combine(datetime.today(), self.check_out)
            delta = check_out_time - check_in_time
            return round(delta.total_seconds() / 3600, 2)
        return 0
