/**
 * @fileoverview Point d'entrée principal du tableau de bord (dashboard.html).
 *
 * Ce module est le cœur de l'application. Il gère :
 *
 *  **État global**
 *   - AppState : objet singleton contenant toutes les données en mémoire.
 *
 *  **Initialisation**
 *   - Vérification de l'authentification JWT au chargement de la page.
 *   - Chargement des données depuis l'API REST.
 *
 *  **Navigation**
 *   - Routage entre les sections (dashboard, employees, departments, leaves, attendance, reports).
 *   - Gestion du menu mobile (sidebar overlay).
 *
 *  **Dashboard**
 *   - Calcul et affichage des statistiques (employés, présences, congés du jour).
 *   - Liste des 5 derniers employés recrutés.
 *   - Liste des 5 demandes de congé les plus récentes.
 *
 *  **Authentification**
 *   - Déconnexion avec confirmation (modal).
 *   - Application des permissions UI selon le rôle.
 *
 * Les modules spécialisés (dashboard-employees.js, dashboard-leaves.js, etc.)
 * dépendent de ce fichier pour accéder à AppState et aux wrappers API.
 */

// ===========================
// État global de l'application
// ===========================

/**
 * @typedef {Object} Employee
 * @property {number}  id           - Identifiant unique.
 * @property {string}  firstName    - Prénom.
 * @property {string}  lastName     - Nom.
 * @property {string}  email        - Adresse e-mail.
 * @property {string}  phone        - Numéro de téléphone.
 * @property {string}  department   - Nom de l'entreprise (Department.name).
 * @property {number}  departmentId - ID de l'entreprise.
 * @property {string}  position     - Poste occupé.
 * @property {string}  hireDate     - Date d'embauche (ISO 8601).
 * @property {number}  salary       - Salaire mensuel.
 * @property {string}  matricule    - Numéro matricule.
 * @property {string}  cnps         - Numéro CNPS.
 * @property {string}  address      - Adresse complète.
 * @property {string}  status       - 'active' | 'inactive' | 'on_leave'.
 */

/**
 * @typedef {Object} AppStateShape
 * @property {Object|null} currentUser    - Utilisateur connecté (ou null si non authentifié).
 * @property {Employee[]}  employees      - Liste de tous les employés visibles.
 * @property {Object[]}    departments    - Liste des entreprises.
 * @property {Object[]}    leaves         - Liste des demandes de congé.
 * @property {Object[]}    attendance     - Liste des enregistrements de présence.
 * @property {string}      currentSection - Section active : 'dashboard' | 'employees' | …
 */

/**
 * Singleton d'état global de l'application.
 * Toutes les données chargées depuis l'API sont stockées ici
 * et partagées entre les modules du dashboard.
 *
 * @type {AppStateShape}
 */
const AppState = {
    currentUser: null,
    employees: [],
    departments: [],
    leaves: [],
    attendance: [],
    currentSection: 'dashboard'
};

// ===========================
// Initialisation
// ===========================

/**
 * Point d'entrée : exécuté au chargement du DOM.
 * Vérifie l'authentification, charge les données et attache les écouteurs.
 */
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
    initializeApp();
    setupEventListeners();
    // Démarrer le système d'alarmes congés (après que AppState.currentUser est défini)
    if (typeof initNotifications === 'function') {
        initNotifications();
    }
});

/**
 * Vérifie que l'utilisateur est bien authentifié et a le droit d'accéder
 * au tableau de bord.
 *
 * - Redirige vers login.html si le token JWT est absent ou expiré.
 * - Redirige les employés (role = 'employee') vers employee-profile.html.
 * - Met à jour l'affichage du nom et du rôle dans la barre latérale.
 * - Applique les restrictions d'interface selon le rôle (applyRolePermissions).
 *
 * @returns {void}
 */
function checkAuthentication() {
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    const currentUser = getCurrentUser();
    if (!currentUser) {
        handleLogoutRedirect();
        return;
    }

    // Les employés ont leur propre espace dédié
    if (currentUser.role === 'employee') {
        window.location.href = 'employee-profile.html';
        return;
    }

    AppState.currentUser = currentUser;

    // Afficher les informations de l'utilisateur dans la sidebar
    const userNameEl = document.getElementById('currentUserName');
    const userRoleEl = document.getElementById('currentUserRole');
    if (userNameEl) userNameEl.textContent = AppState.currentUser.name || AppState.currentUser.username;
    if (userRoleEl) userRoleEl.textContent = getRoleLabel(AppState.currentUser.role);

    applyRolePermissions();
}

/**
 * Charge les données depuis l'API et affiche la section dashboard.
 *
 * @returns {Promise<void>}
 */
async function initializeApp() {
    await loadDataFromAPI();
    renderDashboard();
}

/**
 * Charge toutes les ressources nécessaires depuis l'API REST
 * et normalise leur structure pour l'utilisation frontend.
 *
 * Les entités chargées :
 *  - Departments  → AppState.departments
 *  - Employees    → AppState.employees   (normalisation snake_case → camelCase)
 *  - Leaves       → AppState.leaves      (normalisation snake_case → camelCase)
 *  - Attendances  → AppState.attendance  (normalisation snake_case → camelCase)
 *
 * En cas d'erreur réseau, toutes les listes sont réinitialisées à [].
 *
 * @returns {Promise<void>}
 */
async function loadDataFromAPI() {
    try {
        const departments = await apiGet(API_ENDPOINTS.DEPARTMENTS);
        AppState.departments = departments ? (departments.results || departments) : [];

        const employees = await apiGet(API_ENDPOINTS.EMPLOYEES);
        AppState.employees = employees
            ? (employees.results || employees).map(emp => ({
                id: emp.id,
                firstName: emp.first_name,
                lastName: emp.last_name,
                email: emp.email,
                phone: emp.phone,
                department: emp.department_name || emp.department,
                departmentId: emp.department,
                direction: emp.direction,
                position: emp.position,
                hireDate: emp.hire_date,
                salary: emp.salary,
                matricule: emp.matricule,
                cnps: emp.cnps,
                address: emp.address,
                status: emp.status
            }))
            : [];

        // Filtrage côté client selon le rôle (couche de sécurité supplémentaire)
        const role = AppState.currentUser?.role;
        if (role === 'entreprise') {
            const managedDeptName = AppState.currentUser?.managed_department?.name;
            if (managedDeptName) {
                AppState.employees = AppState.employees.filter(emp => emp.department === managedDeptName);
            }
        } else if (role === 'manager') {
            const managedDirections = AppState.currentUser?.managed_directions || [];
            if (managedDirections.length > 0) {
                AppState.employees = AppState.employees.filter(emp => managedDirections.includes(emp.direction));
            } else {
                AppState.employees = [];
            }
        }

        const leaves = await apiGet(API_ENDPOINTS.LEAVES);
        AppState.leaves = leaves
            ? (leaves.results || leaves).map(leave => ({
                id: leave.id,
                employeeId: leave.employee,
                employeeName: leave.employee_name,
                type: leave.leave_type,
                startDate: leave.start_date,
                endDate: leave.end_date,
                days: leave.days_count,
                reason: leave.reason,
                status: leave.status
            }))
            : [];

        const attendance = await apiGet(API_ENDPOINTS.ATTENDANCES);
        AppState.attendance = attendance
            ? (attendance.results || attendance).map(att => ({
                id: att.id,
                employeeId: att.employee,
                employeeName: att.employee_name,
                date: att.date,
                checkIn: att.check_in,
                checkOut: att.check_out,
                hours: att.hours_worked,
                status: att.status
            }))
            : [];

    } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        AppState.departments = [];
        AppState.employees = [];
        AppState.leaves = [];
        AppState.attendance = [];
    }
}

/**
 * Stub conservé pour compatibilité.
 * Les données ne sont plus sauvegardées localement ; tout est géré par l'API.
 *
 * @returns {void}
 */
function saveToLocalStorage() {
    // Ne plus sauvegarder localement - les données sont sur le serveur
}

// ===========================
// Gestion des événements
// ===========================

/**
 * Attache tous les écouteurs d'événements de la page dashboard.
 *
 * Couvre : menu mobile, déconnexion, navigation latérale,
 * boutons d'ajout, soumission de formulaires, fermeture de modals,
 * recherche, filtres et onglets de congés.
 *
 * @returns {void}
 */
function setupEventListeners() {
    // ---- Menu mobile (sidebar) ----
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const sidebar = document.querySelector('.sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('mobile-open');
            sidebarOverlay?.classList.toggle('active');
        });
    }

    if (sidebarOverlay) {
        sidebarOverlay.addEventListener('click', () => {
            sidebar?.classList.remove('mobile-open');
            sidebarOverlay.classList.remove('active');
        });
    }

    // ---- Déconnexion ----
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);
    document.getElementById('logoutBtnBottom')?.addEventListener('click', handleLogout);

    // ---- Navigation latérale ----
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', handleNavigation);
    });

    // ---- Boutons d'ajout ----
    document.getElementById('addEmployeeBtn')?.addEventListener('click', () => openEmployeeModal());
    document.getElementById('addDepartmentBtn')?.addEventListener('click', () => openDepartmentModal());
    document.getElementById('requestLeaveBtn')?.addEventListener('click', () => openLeaveModal());
    document.getElementById('markAttendanceBtn')?.addEventListener('click', () => openAttendanceModal());

    // ---- Formulaires ----
    document.getElementById('employeeForm')?.addEventListener('submit', handleEmployeeSubmit);
    document.getElementById('departmentForm')?.addEventListener('submit', handleDepartmentSubmit);
    document.getElementById('leaveForm')?.addEventListener('submit', handleLeaveSubmit);
    document.getElementById('attendanceForm')?.addEventListener('submit', handleAttendanceSubmit);

    // ---- Fermeture des modals (bouton ×) ----
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.modal').classList.remove('active');
        });
    });

    // ---- Fermeture des modals (clic sur l'arrière-plan) ----
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });

    // ---- Recherche et filtres employés ----
    document.getElementById('searchEmployee')?.addEventListener('input', handleEmployeeSearch);
    document.getElementById('filterDepartment')?.addEventListener('change', renderEmployeesTable);
    document.getElementById('filterPosition')?.addEventListener('change', renderEmployeesTable);

    // ---- Onglets de filtrage des congés ----
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', handleTabClick);
    });
}

// ===========================
// Authentification
// ===========================

/**
 * Ouvre le modal de confirmation de déconnexion.
 * N'effectue pas la déconnexion directement — attend confirmLogout().
 *
 * @returns {void}
 */
function handleLogout() {
    openLogoutModal();
}

/**
 * Affiche le modal de déconnexion avec le nom et le rôle de l'utilisateur actuel.
 *
 * @returns {void}
 */
function openLogoutModal() {
    const modal = document.getElementById('logoutModal');
    const currentUser = AppState.currentUser;
    const modalNameEl = document.getElementById('modalCurrentUserName');
    const modalRoleEl = document.getElementById('modalCurrentUserRole');
    if (modalNameEl) modalNameEl.textContent = currentUser.name;
    if (modalRoleEl) modalRoleEl.textContent = getRoleLabel(currentUser.role);
    modal.classList.add('active');
}

/**
 * Effectue la déconnexion effective : supprime les tokens du stockage local
 * et redirige vers la page de connexion.
 *
 * Appelée par le bouton "Confirmer" du modal de déconnexion.
 *
 * @returns {void}
 */
function confirmLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('currentUser');
    window.location.href = 'login.html';
}

/**
 * Retourne le libellé français d'un rôle utilisateur.
 *
 * @param {string} role - Code interne : 'admin' | 'manager' | 'entreprise' | 'employee'.
 * @returns {string} Libellé lisible, ou le code brut si inconnu.
 */
function getRoleLabel(role) {
    const labels = {
        'admin': 'Administrateur',
        'manager': 'Manager',
        'entreprise': 'Entreprise',
        'employee': 'Employé'
    };
    return labels[role] || role;
}

/**
 * Masque les éléments de l'interface auxquels le rôle actuel n'a pas accès.
 *
 * Règles appliquées :
 *  - employee  : masque les boutons d'ajout et d'action (modifier/supprimer).
 *  - entreprise : masque le bouton d'ajout d'entreprise.
 *
 * @returns {void}
 */
function applyRolePermissions() {
    const role = AppState.currentUser.role;

    if (role === 'employee') {
        document.getElementById('addEmployeeBtn')?.classList.add('hidden');
        document.getElementById('addDepartmentBtn')?.classList.add('hidden');
        document.querySelectorAll('.action-btn.edit, .action-btn.delete').forEach(btn => {
            btn.classList.add('hidden');
        });
    }

    if (role === 'entreprise') {
        document.getElementById('addEmployeeBtn')?.classList.add('hidden');
        document.getElementById('addDepartmentBtn')?.classList.add('hidden');
        document.getElementById('requestLeaveBtn')?.classList.add('hidden');
        document.querySelectorAll('.action-btn.edit, .action-btn.delete').forEach(btn => {
            btn.classList.add('hidden');
        });
    }

    if (role === 'manager') {
        document.getElementById('addEmployeeBtn')?.classList.add('hidden');
        document.getElementById('addDepartmentBtn')?.classList.add('hidden');
        document.getElementById('requestLeaveBtn')?.classList.add('hidden');
        document.querySelectorAll('.action-btn.edit, .action-btn.delete').forEach(btn => {
            btn.classList.add('hidden');
        });
    }
}

// ===========================
// Navigation
// ===========================

/**
 * Gère le clic sur un élément de navigation latérale.
 *
 * - Met à jour la classe `active` sur les éléments de navigation.
 * - Affiche la section `.content-section` correspondante.
 * - Ferme la sidebar en mode mobile.
 * - Délègue le rendu de la section à renderSection().
 *
 * @this {HTMLElement} Élément `.nav-item` cliqué.
 * @param {MouseEvent} e - Événement de clic.
 * @returns {void}
 */
function handleNavigation(e) {
    e.preventDefault();

    const section = this.dataset.section;

    // Mettre à jour l'état actif de la navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');

    // Afficher la section demandée
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(section + 'Section').classList.add('active');

    AppState.currentSection = section;

    // Fermer la sidebar en mode mobile après navigation
    const sidebar = document.querySelector('.sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    sidebar?.classList.remove('mobile-open');
    sidebarOverlay?.classList.remove('active');

    renderSection(section);
}

/**
 * Délègue le rendu initial de la section activée à la fonction appropriée.
 *
 * @param {string} section - Identifiant de la section :
 *   'dashboard' | 'employees' | 'departments' | 'leaves' | 'attendance' | 'reports'.
 * @returns {void}
 */
function renderSection(section) {
    switch(section) {
        case 'dashboard':
            renderDashboard();
            break;
        case 'employees':
            renderEmployeesTable();
            populateDepartmentFilters();
            break;
        case 'departments':
            renderDepartmentsGrid();
            break;
        case 'leaves':
            renderLeavesTable();
            break;
        case 'attendance':
            renderAttendanceTable();
            renderAttendanceCalendar();
            break;
        case 'reports':
            // Les rapports sont générés à la demande via downloadReport()
            break;
    }
}

// ===========================
// Dashboard — Statistiques et listes
// ===========================

/**
 * Met à jour toutes les statistiques et listes du tableau de bord principal.
 *
 * Statistiques mises à jour :
 *  - #totalEmployees   : nombre total d'employés visibles.
 *  - #totalDepartments : nombre total d'entreprises.
 *  - #presentToday     : employés marqués 'present' aujourd'hui.
 *  - #onLeaveToday     : employés en congé approuvé aujourd'hui.
 *
 * Listes mises à jour :
 *  - #recentEmployees  : 5 derniers employés recrutés.
 *  - #pendingLeaves    : 5 demandes de congé les plus récentes.
 *
 * @returns {void}
 */
function renderDashboard() {
    document.getElementById('totalEmployees').textContent = AppState.employees.length;
    document.getElementById('totalDepartments').textContent = AppState.departments.length;

    const today = new Date().toISOString().split('T')[0];

    // Employés présents aujourd'hui
    const presentToday = AppState.attendance.filter(a => a.date === today && a.status === 'present').length;
    document.getElementById('presentToday').textContent = presentToday;

    // Employés en congé approuvé couvrant la date du jour
    const onLeaveToday = AppState.leaves.filter(l => {
        return l.status === 'approved' &&
               new Date(l.startDate) <= new Date(today) &&
               new Date(l.endDate) >= new Date(today);
    }).length;
    document.getElementById('onLeaveToday').textContent = onLeaveToday;

    renderRecentEmployees();
    renderPendingLeaves();
}

/**
 * Affiche les 5 employés les plus récemment recrutés dans la section
 * #recentEmployees du tableau de bord.
 *
 * Les employés sont triés par date d'embauche décroissante.
 * Les initiales sont calculées à partir du prénom et du nom.
 * Toutes les données texte sont échappées via escapeHtml().
 *
 * @returns {void}
 */
function renderRecentEmployees() {
    const recentEmployees = AppState.employees
        .sort((a, b) => new Date(b.hireDate) - new Date(a.hireDate))
        .slice(0, 5);

    const container = document.getElementById('recentEmployees');
    container.innerHTML = recentEmployees.map(emp => `
        <div class="list-item">
            <div class="list-item-avatar">${escapeHtml(emp.firstName.charAt(0))}${escapeHtml(emp.lastName.charAt(0))}</div>
            <div class="list-item-info">
                <div class="name">${escapeHtml(emp.firstName)} ${escapeHtml(emp.lastName)}</div>
                <div class="detail">${escapeHtml(emp.position)} - ${escapeHtml(emp.department)}</div>
            </div>
            <span class="status-badge status-${emp.status}">${getStatusLabel(emp.status)}</span>
        </div>
    `).join('');
}

/**
 * Affiche les 5 demandes de congé les plus récentes dans la section
 * #pendingLeaves du tableau de bord.
 *
 * Les congés sont triés par date de début décroissante (tous statuts confondus).
 * Les initiales de l'employé sont extraites du champ `employeeName`.
 * Les données texte sont échappées via escapeHtml().
 *
 * @returns {void}
 */
function renderPendingLeaves() {
    const recentLeaves = AppState.leaves
        .sort((a, b) => new Date(b.startDate) - new Date(a.startDate))
        .slice(0, 5);

    const container = document.getElementById('pendingLeaves');

    if (recentLeaves.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 1rem; color: var(--text-secondary);">Aucune demande de congé</p>';
        return;
    }

    container.innerHTML = recentLeaves.map(leave => {
        // Calcul des initiales à partir du nom complet de l'employé
        const nameParts = (leave.employeeName || '').split(' ');
        const initials = nameParts.length >= 2
            ? nameParts[0].charAt(0) + nameParts[nameParts.length - 1].charAt(0)
            : (nameParts[0] || '').substring(0, 2);

        return `
        <div class="list-item">
            <div class="list-item-avatar">${escapeHtml(initials)}</div>
            <div class="list-item-info">
                <div class="name">${escapeHtml(leave.employeeName)}</div>
                <div class="detail">${getLeaveTypeLabel(leave.type)} - ${formatDate(leave.startDate)} au ${formatDate(leave.endDate)} (${leave.days} jours)</div>
            </div>
            <span class="status-badge status-${leave.status}">${getLeaveStatusLabel(leave.status)}</span>
        </div>
    `;
    }).join('');
}

// ===========================
// Exports globaux
// ===========================
window.confirmLogout = confirmLogout;
