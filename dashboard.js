// ===========================
// État Global de l'Application
// ===========================
const AppState = {
    currentUser: null,
    employees: [],
    departments: [],
    leaves: [],
    attendance: [],
    currentSection: 'dashboard'
};

// Entreprises par défaut
const DEFAULT_DEPARTMENTS = [
    { id: 1, name: 'Ressources Humaines', manager: 'Marie Dupont', description: 'Gestion du personnel et recrutement', employees: 8 },
    { id: 2, name: 'Informatique', manager: 'Jean Martin', description: 'Développement et support technique', employees: 15 },
    { id: 3, name: 'Marketing', manager: 'Sophie Bernard', description: 'Communication et stratégie marketing', employees: 10 },
    { id: 4, name: 'Finance', manager: 'Pierre Dubois', description: 'Comptabilité et gestion financière', employees: 6 },
    { id: 5, name: 'Commercial', manager: 'Luc Moreau', description: 'Ventes et relations clients', employees: 12 }
];

// Employés par défaut
const DEFAULT_EMPLOYEES = [
    { id: 1, firstName: 'Marie', lastName: 'Dupont', email: 'marie.dupont@company.com', phone: '0612345678', department: 'Ressources Humaines', position: 'DRH', hireDate: '2020-01-15', salary: 55000, address: '10 Rue de Paris, 75001 Paris', status: 'active' },
    { id: 2, firstName: 'Jean', lastName: 'Martin', email: 'jean.martin@company.com', phone: '0623456789', department: 'Informatique', position: 'Développeur Senior', hireDate: '2019-03-20', salary: 48000, address: '25 Avenue des Champs, 75008 Paris', status: 'active' },
    { id: 3, firstName: 'Sophie', lastName: 'Bernard', email: 'sophie.bernard@company.com', phone: '0634567890', department: 'Marketing', position: 'Chef de Projet', hireDate: '2021-06-10', salary: 42000, address: '5 Boulevard Haussmann, 75009 Paris', status: 'active' },
    { id: 4, firstName: 'Pierre', lastName: 'Dubois', email: 'pierre.dubois@company.com', phone: '0645678901', department: 'Finance', position: 'Comptable', hireDate: '2018-09-05', salary: 38000, address: '15 Rue Lafayette, 75010 Paris', status: 'active' },
    { id: 5, firstName: 'Luc', lastName: 'Moreau', email: 'luc.moreau@company.com', phone: '0656789012', department: 'Commercial', position: 'Commercial Senior', hireDate: '2020-11-12', salary: 45000, address: '30 Rue de Rivoli, 75004 Paris', status: 'active' }
];

// Congés par défaut
const DEFAULT_LEAVES = [
    { id: 1, employeeId: 1, employeeName: 'Marie Dupont', type: 'paid', startDate: '2026-02-15', endDate: '2026-02-20', days: 5, reason: 'Vacances familiales', status: 'pending' },
    { id: 2, employeeId: 2, employeeName: 'Jean Martin', type: 'sick', startDate: '2026-01-20', endDate: '2026-01-22', days: 2, reason: 'Grippe', status: 'approved' },
    { id: 3, employeeId: 3, employeeName: 'Sophie Bernard', type: 'paid', startDate: '2026-03-01', endDate: '2026-03-07', days: 7, reason: 'Voyage', status: 'pending' }
];

// Présences par défaut
const DEFAULT_ATTENDANCE = [
    { id: 1, employeeId: 1, employeeName: 'Marie Dupont', date: '2026-01-22', checkIn: '08:30', checkOut: '17:30', hours: 9, status: 'present' },
    { id: 2, employeeId: 2, employeeName: 'Jean Martin', date: '2026-01-22', checkIn: '09:00', checkOut: '18:00', hours: 9, status: 'present' },
    { id: 3, employeeId: 3, employeeName: 'Sophie Bernard', date: '2026-01-22', checkIn: '08:45', checkOut: '17:45', hours: 9, status: 'present' }
];

// ===========================
// Initialisation
// ===========================
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si l'utilisateur est connecté
    checkAuthentication();

    initializeApp();
    setupEventListeners();
});

function checkAuthentication() {
    // Vérifier le token JWT
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    // Charger les informations de l'utilisateur depuis sessionStorage
    const currentUser = getCurrentUser();
    if (!currentUser) {
        handleLogoutRedirect();
        return;
    }

    // Bloquer l'accès aux employés - ils doivent utiliser leur Espace Contractuel
    if (currentUser.role === 'employee') {
        window.location.href = 'employee-profile.html';
        return;
    }

    AppState.currentUser = currentUser;

    // Afficher les informations de l'utilisateur
    const userNameEl = document.getElementById('currentUserName');
    const userRoleEl = document.getElementById('currentUserRole');
    if (userNameEl) userNameEl.textContent = AppState.currentUser.name || AppState.currentUser.username;
    if (userRoleEl) userRoleEl.textContent = getRoleLabel(AppState.currentUser.role);

    // Appliquer les permissions basées sur le rôle
    applyRolePermissions();
}

async function initializeApp() {
    // Charger les données depuis l'API
    await loadDataFromAPI();

    // Initialiser le dashboard
    renderDashboard();
}

async function loadDataFromAPI() {
    try {
        // Charger les entreprises
        const departments = await apiGet(API_ENDPOINTS.DEPARTMENTS);
        if (departments) {
            // Adapter le format pour la compatibilité frontend
            AppState.departments = departments.results || departments;
        } else {
            AppState.departments = DEFAULT_DEPARTMENTS;
        }

        // Charger les employés
        const employees = await apiGet(API_ENDPOINTS.EMPLOYEES);
        if (employees) {
            // Adapter le format pour la compatibilité frontend
            AppState.employees = (employees.results || employees).map(emp => ({
                id: emp.id,
                firstName: emp.first_name,
                lastName: emp.last_name,
                email: emp.email,
                phone: emp.phone,
                department: emp.department_name || emp.department,
                departmentId: emp.department,
                position: emp.position,
                hireDate: emp.hire_date,
                salary: emp.salary,
                matricule: emp.matricule,
                cnps: emp.cnps,
                address: emp.address,
                status: emp.status
            }));
        } else {
            AppState.employees = DEFAULT_EMPLOYEES;
        }

        // Charger les congés
        const leaves = await apiGet(API_ENDPOINTS.LEAVES);
        if (leaves) {
            AppState.leaves = (leaves.results || leaves).map(leave => ({
                id: leave.id,
                employeeId: leave.employee,
                employeeName: leave.employee_name,
                type: leave.leave_type,
                startDate: leave.start_date,
                endDate: leave.end_date,
                days: leave.days_count,
                reason: leave.reason,
                status: leave.status
            }));
        } else {
            AppState.leaves = DEFAULT_LEAVES;
        }

        // Charger les présences
        const attendance = await apiGet(API_ENDPOINTS.ATTENDANCES);
        if (attendance) {
            AppState.attendance = (attendance.results || attendance).map(att => ({
                id: att.id,
                employeeId: att.employee,
                employeeName: att.employee_name,
                date: att.date,
                checkIn: att.check_in,
                checkOut: att.check_out,
                hours: att.hours_worked,
                status: att.status
            }));
        } else {
            AppState.attendance = DEFAULT_ATTENDANCE;
        }

    } catch (error) {
        console.error('Erreur lors du chargement des données:', error);
        // Utiliser les données par défaut en cas d'erreur
        AppState.departments = DEFAULT_DEPARTMENTS;
        AppState.employees = DEFAULT_EMPLOYEES;
        AppState.leaves = DEFAULT_LEAVES;
        AppState.attendance = DEFAULT_ATTENDANCE;
    }
}

function saveToLocalStorage() {
    // Ne plus sauvegarder localement - les données sont sur le serveur
    // Cette fonction est conservée pour compatibilité mais ne fait rien
}

// ===========================
// Gestion des Événements
// ===========================
function setupEventListeners() {
    // Menu mobile
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

    // Déconnexion
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
    }

    const logoutBtnBottom = document.getElementById('logoutBtnBottom');
    if (logoutBtnBottom) {
        logoutBtnBottom.addEventListener('click', handleLogout);
    }

    // Navigation
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', handleNavigation);
    });

    // Boutons d'ajout
    document.getElementById('addEmployeeBtn')?.addEventListener('click', () => openEmployeeModal());
    document.getElementById('addDepartmentBtn')?.addEventListener('click', () => openDepartmentModal());
    document.getElementById('requestLeaveBtn')?.addEventListener('click', () => openLeaveModal());
    document.getElementById('markAttendanceBtn')?.addEventListener('click', () => openAttendanceModal());

    // Formulaires
    document.getElementById('employeeForm')?.addEventListener('submit', handleEmployeeSubmit);
    document.getElementById('departmentForm')?.addEventListener('submit', handleDepartmentSubmit);
    document.getElementById('leaveForm')?.addEventListener('submit', handleLeaveSubmit);
    document.getElementById('attendanceForm')?.addEventListener('submit', handleAttendanceSubmit);

    // Fermeture des modals
    document.querySelectorAll('.close-modal').forEach(btn => {
        btn.addEventListener('click', function() {
            this.closest('.modal').classList.remove('active');
        });
    });

    // Fermer modal en cliquant à l'extérieur
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.remove('active');
            }
        });
    });

    // Recherche
    document.getElementById('searchEmployee')?.addEventListener('input', handleEmployeeSearch);
    // Filtres
    document.getElementById('filterDepartment')?.addEventListener('change', renderEmployeesTable);
    document.getElementById('filterPosition')?.addEventListener('change', renderEmployeesTable);

    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', handleTabClick);
    });
}

// ===========================
// Authentification
// ===========================
function handleLogout() {
    // Ouvrir le modal de déconnexion/changement de compte
    openLogoutModal();
}

function openLogoutModal() {
    const modal = document.getElementById('logoutModal');

    // Mettre à jour les informations de l'utilisateur dans le modal
    const currentUser = AppState.currentUser;
    const modalNameEl = document.getElementById('modalCurrentUserName');
    const modalRoleEl = document.getElementById('modalCurrentUserRole');
    if (modalNameEl) modalNameEl.textContent = currentUser.name;
    if (modalRoleEl) modalRoleEl.textContent = getRoleLabel(currentUser.role);

    // Afficher le modal
    modal.classList.add('active');
}

function switchAccount(newRole) {
    // Obtenir les credentials par défaut pour chaque rôle
    const accounts = {
        'admin': { username: 'admin', name: 'Administrateur', role: 'admin' },
        'manager': { username: 'manager', name: 'Manager', role: 'manager' },
        'employee': { username: 'employee', name: 'Employé', role: 'employee' }
    };

    const newAccount = accounts[newRole];

    if (newAccount) {
        // Mettre à jour la session avec le nouveau compte
        sessionStorage.setItem('currentUser', JSON.stringify(newAccount));
        AppState.currentUser = newAccount;

        // Mettre à jour l'affichage
        const switchNameEl = document.getElementById('currentUserName');
        const switchRoleEl = document.getElementById('currentUserRole');
        if (switchNameEl) switchNameEl.textContent = newAccount.name;
        if (switchRoleEl) switchRoleEl.textContent = getRoleLabel(newAccount.role);

        // Appliquer les permissions du nouveau rôle
        applyRolePermissions();

        // Fermer le modal
        closeModal('logoutModal');

        // Recharger le dashboard
        renderDashboard();

        // Afficher une notification
        alert(`Vous êtes maintenant connecté en tant que ${getRoleLabel(newRole)}`);
    }
}

function confirmLogout() {
    // Supprimer les tokens JWT et les informations de session
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('currentUser');

    // Rediriger vers la page de connexion
    window.location.href = 'login.html';
}

function getRoleLabel(role) {
    const labels = {
        'admin': 'Administrateur',
        'manager': 'Manager',
        'entreprise': 'Entreprise',
        'employee': 'Employé'
    };
    return labels[role] || role;
}

function applyRolePermissions() {
    const role = AppState.currentUser.role;

    // Les employés ne peuvent pas ajouter/modifier/supprimer
    if (role === 'employee') {
        document.getElementById('addEmployeeBtn')?.classList.add('hidden');
        document.getElementById('addDepartmentBtn')?.classList.add('hidden');

        // Masquer les boutons d'action dans les tableaux
        document.querySelectorAll('.action-btn.edit, .action-btn.delete').forEach(btn => {
            btn.classList.add('hidden');
        });
    }

    // Entreprise : ne peut pas gérer les entreprises
    if (role === 'entreprise') {
        document.getElementById('addDepartmentBtn')?.classList.add('hidden');
    }
}

// ===========================
// Navigation
// ===========================
function handleNavigation(e) {
    e.preventDefault();

    const section = this.dataset.section;

    // Mettre à jour la navigation active
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    this.classList.add('active');

    // Afficher la section correspondante
    document.querySelectorAll('.content-section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(section + 'Section').classList.add('active');

    AppState.currentSection = section;

    // Fermer le menu mobile après navigation
    const sidebar = document.querySelector('.sidebar');
    const sidebarOverlay = document.getElementById('sidebarOverlay');
    sidebar?.classList.remove('mobile-open');
    sidebarOverlay?.classList.remove('active');

    // Charger les données de la section
    renderSection(section);
}

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
            // Les rapports sont statiques pour le moment
            break;
    }
}

// ===========================
// Dashboard
// ===========================
function renderDashboard() {
    // Statistiques
    document.getElementById('totalEmployees').textContent = AppState.employees.length;
    document.getElementById('totalDepartments').textContent = AppState.departments.length;

    const today = new Date().toISOString().split('T')[0];
    const presentToday = AppState.attendance.filter(a => a.date === today && a.status === 'present').length;
    document.getElementById('presentToday').textContent = presentToday;

    const onLeaveToday = AppState.leaves.filter(l => {
        return l.status === 'approved' &&
               new Date(l.startDate) <= new Date(today) &&
               new Date(l.endDate) >= new Date(today);
    }).length;
    document.getElementById('onLeaveToday').textContent = onLeaveToday;

    // Employés récents
    renderRecentEmployees();

    // Demandes de congés en attente
    renderPendingLeaves();
}

function renderRecentEmployees() {
    const recentEmployees = AppState.employees
        .sort((a, b) => new Date(b.hireDate) - new Date(a.hireDate))
        .slice(0, 5);

    const container = document.getElementById('recentEmployees');
    container.innerHTML = recentEmployees.map(emp => `
        <div class="list-item">
            <div class="list-item-avatar">${emp.firstName.charAt(0)}${emp.lastName.charAt(0)}</div>
            <div class="list-item-info">
                <div class="name">${emp.firstName} ${emp.lastName}</div>
                <div class="detail">${emp.position} - ${emp.department}</div>
            </div>
            <span class="status-badge status-${emp.status}">${getStatusLabel(emp.status)}</span>
        </div>
    `).join('');
}

function renderPendingLeaves() {
    // Afficher les congés récents (tous statuts), triés par date de création
    const recentLeaves = AppState.leaves
        .sort((a, b) => new Date(b.startDate) - new Date(a.startDate))
        .slice(0, 5);

    const container = document.getElementById('pendingLeaves');

    if (recentLeaves.length === 0) {
        container.innerHTML = '<p style="text-align: center; padding: 1rem; color: var(--text-secondary);">Aucune demande de congé</p>';
        return;
    }

    container.innerHTML = recentLeaves.map(leave => {
        // Extraire les initiales du nom de l'employé
        const nameParts = (leave.employeeName || '').split(' ');
        const initials = nameParts.length >= 2
            ? nameParts[0].charAt(0) + nameParts[nameParts.length - 1].charAt(0)
            : (nameParts[0] || '').substring(0, 2);

        return `
        <div class="list-item">
            <div class="list-item-avatar">${initials}</div>
            <div class="list-item-info">
                <div class="name">${leave.employeeName}</div>
                <div class="detail">${getLeaveTypeLabel(leave.type)} - ${formatDate(leave.startDate)} au ${formatDate(leave.endDate)} (${leave.days} jours)</div>
            </div>
            <span class="status-badge status-${leave.status}">${getLeaveStatusLabel(leave.status)}</span>
        </div>
    `;
    }).join('');
}

// ===========================
// Gestion des Employés
// ===========================
function renderEmployeesTable() {
    const searchTerm = document.getElementById('searchEmployee')?.value.toLowerCase() || '';
    const filterDept = document.getElementById('filterDepartment')?.value || '';
    const filterPos = document.getElementById('filterPosition')?.value || '';

    let filteredEmployees = AppState.employees.filter(emp => {
        const matchSearch = emp.firstName.toLowerCase().includes(searchTerm) ||
                          emp.lastName.toLowerCase().includes(searchTerm) ||
                          emp.email.toLowerCase().includes(searchTerm);
        const matchDept = !filterDept || emp.department === filterDept;
        const matchPos = !filterPos || emp.position === filterPos;

        return matchSearch && matchDept && matchPos;
    });

    const tbody = document.getElementById('employeesTableBody');
    tbody.innerHTML = filteredEmployees.map(emp => `
        <tr>
            <td>#${emp.id}</td>
            <td>${emp.firstName} ${emp.lastName}</td>
            <td>${emp.email}</td>
            <td>${emp.department}</td>
            <td>${emp.position}</td>
            <td>${formatDate(emp.hireDate)}</td>
            <td><span class="status-badge status-${emp.status}">${getStatusLabel(emp.status)}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn download" onclick="downloadEmployeeProfile(${emp.id})" title="Télécharger le profil">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="action-btn edit" onclick="editEmployee(${emp.id})">
                        <i class="fas fa-edit"></i> Modifier
                    </button>
                    <button class="action-btn delete" onclick="deleteEmployee(${emp.id})">
                        <i class="fas fa-trash"></i> Supprimer
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
}

function handleEmployeeSearch(e) {
    renderEmployeesTable();
}

function populateDepartmentFilters() {
    const deptSelect = document.getElementById('filterDepartment');
    const empDeptSelect = document.getElementById('empDepartment');

    const deptOptions = AppState.departments.map(dept =>
        `<option value="${dept.name}">${dept.name}</option>`
    ).join('');

    if (deptSelect) {
        deptSelect.innerHTML = '<option value="">Tous les entreprises</option>' + deptOptions;
    }

    if (empDeptSelect) {
        empDeptSelect.innerHTML = '<option value="">Sélectionner...</option>' + deptOptions;
    }

    // Remplir le filtre des postes
    const positions = [...new Set(AppState.employees.map(e => e.position))];
    const posSelect = document.getElementById('filterPosition');
    if (posSelect) {
        posSelect.innerHTML = '<option value="">Tous les postes</option>' +
            positions.map(pos => `<option value="${pos}">${pos}</option>`).join('');
    }
}

function openEmployeeModal(employeeId = null) {
    populateDepartmentFilters();

    const modal = document.getElementById('employeeModal');
    const form = document.getElementById('employeeForm');
    const title = document.getElementById('employeeModalTitle');

    if (employeeId) {
        const employee = AppState.employees.find(e => e.id === employeeId);
        title.textContent = 'Modifier un Employé';

        document.getElementById('empId').value = employee.id;
        document.getElementById('empFirstName').value = employee.firstName;
        document.getElementById('empLastName').value = employee.lastName;
        document.getElementById('empEmail').value = employee.email;
        document.getElementById('empPhone').value = employee.phone;
        document.getElementById('empDepartment').value = employee.department;
        document.getElementById('empPosition').value = employee.position;
        document.getElementById('empHireDate').value = employee.hireDate;
        document.getElementById('empSalary').value = employee.salary;
        document.getElementById('empMatricule').value = employee.matricule || '';
        document.getElementById('empCNPS').value = employee.cnps || '';
        document.getElementById('empAddress').value = employee.address;
    } else {
        title.textContent = 'Ajouter un Employé';
        form.reset();
        document.getElementById('empId').value = '';
    }

    modal.classList.add('active');
}

async function handleEmployeeSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('empId').value;

    // Trouver l'ID du entreprise à partir du nom
    const departmentName = document.getElementById('empDepartment').value;
    const department = AppState.departments.find(d => d.name === departmentName);
    const departmentId = department ? department.id : null;

    // Format API Django (snake_case)
    const employeeData = {
        first_name: document.getElementById('empFirstName').value,
        last_name: document.getElementById('empLastName').value,
        email: document.getElementById('empEmail').value,
        phone: document.getElementById('empPhone').value || '',
        department: departmentId,
        position: document.getElementById('empPosition').value,
        hire_date: document.getElementById('empHireDate').value,
        salary: parseFloat(document.getElementById('empSalary').value) || 0,
        matricule: document.getElementById('empMatricule').value || '',
        cnps: document.getElementById('empCNPS').value || '',
        address: document.getElementById('empAddress').value || '',
        status: 'active'
    };

    try {
        let result;
        if (id) {
            // Modifier via API
            result = await apiPut(API_ENDPOINTS.EMPLOYEE_DETAIL(id), employeeData);
        } else {
            // Créer via API
            result = await apiPost(API_ENDPOINTS.EMPLOYEES, employeeData);
        }

        if (result.ok) {
            await loadDataFromAPI();
            renderDashboard();
            renderEmployeesTable();
            closeModal('employeeModal');
            alert('Employé enregistré avec succès !');
        } else {
            alert('Erreur: ' + JSON.stringify(result.data));
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'enregistrement de l\'employé');
    }
}

function editEmployee(id) {
    openEmployeeModal(id);
}

async function deleteEmployee(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cet employé ?')) {
        try {
            const result = await apiDelete(API_ENDPOINTS.EMPLOYEE_DETAIL(id));
            if (result.ok) {
                await loadDataFromAPI();
                renderDashboard();
                renderEmployeesTable();
                alert('Employé supprimé avec succès !');
            } else {
                alert('Erreur lors de la suppression');
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la suppression de l\'employé');
        }
    }
}

// ===========================
// Gestion des Entreprises
// ===========================
function renderDepartmentsGrid() {
    const grid = document.getElementById('departmentsGrid');

    grid.innerHTML = AppState.departments.map(dept => {
        const employeeCount = AppState.employees.filter(e => e.department === dept.name).length;

        return `
            <div class="department-card">
                <h3>${dept.name}</h3>
                <p>${dept.description}</p>
                <div class="department-stats">
                    <div class="department-stat">
                        <div class="label">Responsable</div>
                        <div class="value" style="font-size: 1rem; color: var(--text-primary);">${dept.manager}</div>
                    </div>
                    <div class="department-stat">
                        <div class="label">Employés</div>
                        <div class="value">${employeeCount}</div>
                    </div>
                </div>
                <div class="department-actions">
                    <button class="action-btn edit" onclick="editDepartment(${dept.id})">
                        <i class="fas fa-edit"></i> Modifier
                    </button>
                    <button class="action-btn delete" onclick="deleteDepartment(${dept.id})">
                        <i class="fas fa-trash"></i> Supprimer
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function openDepartmentModal(deptId = null) {
    const modal = document.getElementById('departmentModal');
    const form = document.getElementById('departmentForm');
    const title = document.getElementById('departmentModalTitle');

    if (deptId) {
        const dept = AppState.departments.find(d => d.id === deptId);
        title.textContent = 'Modifier un Entreprise';

        document.getElementById('deptId').value = dept.id;
        document.getElementById('deptName').value = dept.name;
        document.getElementById('deptManager').value = dept.manager;
        document.getElementById('deptDescription').value = dept.description;
    } else {
        title.textContent = 'Ajouter un Entreprise';
        form.reset();
        document.getElementById('deptId').value = '';
    }

    modal.classList.add('active');
}

async function handleDepartmentSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('deptId').value;
    const departmentData = {
        name: document.getElementById('deptName').value,
        manager: document.getElementById('deptManager').value,
        description: document.getElementById('deptDescription').value
    };

    try {
        let result;
        if (id) {
            // Modifier via API
            result = await apiPut(API_ENDPOINTS.DEPARTMENT_DETAIL(id), departmentData);
        } else {
            // Créer via API
            result = await apiPost(API_ENDPOINTS.DEPARTMENTS, departmentData);
        }

        if (result.ok) {
            // Recharger les données
            await loadDataFromAPI();
            renderDashboard();
            renderDepartmentsGrid();
            populateDepartmentFilters();
            closeModal('departmentModal');
            alert('Entreprise enregistré avec succès !');
        } else {
            alert('Erreur: ' + JSON.stringify(result.data));
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'enregistrement du entreprise');
    }
}

function editDepartment(id) {
    openDepartmentModal(id);
}

async function deleteDepartment(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce entreprise ?')) {
        try {
            const result = await apiDelete(API_ENDPOINTS.DEPARTMENT_DETAIL(id));
            if (result.ok) {
                await loadDataFromAPI();
                renderDashboard();
                renderDepartmentsGrid();
                alert('Entreprise supprimé avec succès !');
            } else {
                alert('Erreur lors de la suppression');
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la suppression du entreprise');
        }
    }
}

// ===========================
// Gestion des Congés
// ===========================
function renderLeavesTable(filter = 'all') {
    let filteredLeaves = AppState.leaves;

    if (filter !== 'all') {
        filteredLeaves = AppState.leaves.filter(l => l.status === filter);
    }

    const role = AppState.currentUser ? AppState.currentUser.role : '';

    const tbody = document.getElementById('leavesTableBody');
    tbody.innerHTML = filteredLeaves.map(leave => {
        // Déterminer les boutons d'action selon le rôle et le statut
        let actionButtons = '';

        if (role === 'admin') {
            // Admin peut approuver à n'importe quelle étape
            if (leave.status === 'pending' || leave.status === 'manager_approved') {
                actionButtons += `
                    <button class="action-btn approve" onclick="approveLeave(${leave.id})">
                        <i class="fas fa-check"></i> Approuver
                    </button>`;
            }
            if (leave.status !== 'approved' && leave.status !== 'rejected') {
                actionButtons += `
                    <button class="action-btn reject" onclick="rejectLeave(${leave.id})">
                        <i class="fas fa-times"></i> Rejeter
                    </button>`;
            }
        } else if (role === 'manager') {
            // Manager : peut valider seulement les "pending"
            if (leave.status === 'pending') {
                actionButtons += `
                    <button class="action-btn approve" onclick="approveLeave(${leave.id})">
                        <i class="fas fa-check"></i> Valider
                    </button>
                    <button class="action-btn reject" onclick="rejectLeave(${leave.id})">
                        <i class="fas fa-times"></i> Rejeter
                    </button>`;
            }
        } else if (role === 'entreprise') {
            if (leave.status === 'pending') {
                // Pending : en attente du manager, l'entreprise ne peut pas encore agir
                actionButtons += `
                    <span class="action-info"><i class="fas fa-hourglass-half"></i> En attente du Manager</span>`;
            } else if (leave.status === 'manager_approved') {
                // Manager a validé : l'entreprise peut maintenant approuver ou rejeter
                actionButtons += `
                    <span class="action-info validated"><i class="fas fa-user-check"></i> Validé Manager</span>
                    <button class="action-btn approve" onclick="approveLeave(${leave.id})">
                        <i class="fas fa-check"></i> Approuver
                    </button>
                    <button class="action-btn reject" onclick="rejectLeave(${leave.id})">
                        <i class="fas fa-times"></i> Rejeter
                    </button>`;
            }
        }

        return `
        <tr>
            <td>#${leave.id}</td>
            <td>${leave.employeeName}</td>
            <td>${getLeaveTypeLabel(leave.type)}</td>
            <td>${formatDate(leave.startDate)}</td>
            <td>${formatDate(leave.endDate)}</td>
            <td>${leave.days} jours</td>
            <td>${leave.reason}</td>
            <td><span class="status-badge status-${leave.status}">${getLeaveStatusLabel(leave.status)}</span></td>
            <td>
                <div class="action-buttons">
                    ${actionButtons}
                    <button class="action-btn delete" onclick="deleteLeave(${leave.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `;
    }).join('');
}

function handleTabClick(e) {
    const tab = e.target.dataset.tab;

    // Mettre à jour les tabs actifs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');

    // Filtrer les congés
    renderLeavesTable(tab);
}

function openLeaveModal() {
    const modal = document.getElementById('leaveModal');
    const form = document.getElementById('leaveForm');
    const empSelect = document.getElementById('leaveEmployee');

    // Remplir la liste des employés
    empSelect.innerHTML = '<option value="">Sélectionner...</option>' +
        AppState.employees.map(emp =>
            `<option value="${emp.id}">${emp.firstName} ${emp.lastName}</option>`
        ).join('');

    form.reset();
    modal.classList.add('active');
}

async function handleLeaveSubmit(e) {
    e.preventDefault();

    const employeeId = parseInt(document.getElementById('leaveEmployee').value);

    // Format API Django (snake_case)
    const leaveData = {
        employee: employeeId,
        leave_type: document.getElementById('leaveType').value,
        start_date: document.getElementById('leaveStartDate').value,
        end_date: document.getElementById('leaveEndDate').value,
        reason: document.getElementById('leaveReason').value || ''
    };

    try {
        const result = await apiPost(API_ENDPOINTS.LEAVES, leaveData);

        if (result.ok) {
            await loadDataFromAPI();
            renderDashboard();
            renderLeavesTable();
            closeModal('leaveModal');
            alert('Demande de congé soumise avec succès !');
        } else {
            alert('Erreur: ' + JSON.stringify(result.data));
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de la soumission de la demande');
    }
}

async function approveLeave(id) {
    try {
        const result = await apiPost(API_ENDPOINTS.LEAVE_APPROVE(id), {});
        if (result.ok) {
            await loadDataFromAPI();
            renderDashboard();
            renderLeavesTable('pending');
            alert('Congé approuvé !');
        } else {
            alert('Erreur lors de l\'approbation');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'approbation du congé');
    }
}

async function rejectLeave(id) {
    try {
        const result = await apiPost(API_ENDPOINTS.LEAVE_REJECT(id), {});
        if (result.ok) {
            await loadDataFromAPI();
            renderDashboard();
            renderLeavesTable('pending');
            alert('Congé rejeté !');
        } else {
            alert('Erreur lors du rejet');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors du rejet du congé');
    }
}

async function deleteLeave(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette demande de congé ?')) {
        try {
            const result = await apiDelete(API_ENDPOINTS.LEAVE_DETAIL(id));
            if (result.ok) {
                await loadDataFromAPI();
                renderDashboard();
                renderLeavesTable();
                alert('Demande de congé supprimée !');
            } else {
                alert('Erreur lors de la suppression');
            }
        } catch (error) {
            console.error('Erreur:', error);
            alert('Erreur lors de la suppression du congé');
        }
    }
}

// ===========================
// Gestion des Présences
// ===========================
function renderAttendanceTable() {
    const tbody = document.getElementById('attendanceTableBody');

    const sortedAttendance = AppState.attendance.sort((a, b) =>
        new Date(b.date) - new Date(a.date)
    );

    tbody.innerHTML = sortedAttendance.map(att => `
        <tr>
            <td>${formatDate(att.date)}</td>
            <td>${att.employeeName}</td>
            <td>${att.checkIn}</td>
            <td>${att.checkOut || '-'}</td>
            <td>${att.hours || '-'} heures</td>
            <td><span class="status-badge status-${att.status}">${getAttendanceStatusLabel(att.status)}</span></td>
        </tr>
    `).join('');
}

function renderAttendanceCalendar() {
    const calendar = document.getElementById('attendanceCalendar');
    const monthText = document.getElementById('currentMonth');

    // Pour simplifier, afficher juste un message
    calendar.innerHTML = '<p style="text-align: center; padding: 2rem; color: var(--text-secondary);">Calendrier des présences - Fonctionnalité à venir</p>';
}

function openAttendanceModal() {
    const modal = document.getElementById('attendanceModal');
    const form = document.getElementById('attendanceForm');
    const empSelect = document.getElementById('attEmployee');

    // Remplir la liste des employés
    empSelect.innerHTML = '<option value="">Sélectionner...</option>' +
        AppState.employees.map(emp =>
            `<option value="${emp.id}">${emp.firstName} ${emp.lastName}</option>`
        ).join('');

    // Définir la date du jour
    document.getElementById('attDate').value = new Date().toISOString().split('T')[0];

    form.reset();
    modal.classList.add('active');
}

async function handleAttendanceSubmit(e) {
    e.preventDefault();

    const employeeId = parseInt(document.getElementById('attEmployee').value);

    // Format API Django (snake_case)
    const attendanceData = {
        employee: employeeId,
        date: document.getElementById('attDate').value,
        check_in: document.getElementById('attCheckIn').value || null,
        check_out: document.getElementById('attCheckOut').value || null,
        status: document.getElementById('attStatus').value
    };

    try {
        const result = await apiPost(API_ENDPOINTS.ATTENDANCES, attendanceData);

        if (result.ok) {
            await loadDataFromAPI();
            renderAttendanceTable();
            closeModal('attendanceModal');
            alert('Présence enregistrée avec succès !');
        } else {
            alert('Erreur: ' + JSON.stringify(result.data));
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur lors de l\'enregistrement de la présence');
    }
}

// ===========================
// Fonctions Utilitaires
// ===========================
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function getStatusLabel(status) {
    const labels = {
        'active': 'Actif',
        'inactive': 'Inactif',
        'pending': 'En attente'
    };
    return labels[status] || status;
}

function getLeaveTypeLabel(type) {
    const labels = {
        'paid': 'Congé Payé',
        'sick': 'Maladie',
        'unpaid': 'Sans Solde',
        'parental': 'Parental',
        'other': 'Autre'
    };
    return labels[type] || type;
}

function getLeaveStatusLabel(status) {
    const labels = {
        'pending': 'En attente',
        'manager_approved': 'Validé Manager',
        'approved': 'Approuvé',
        'rejected': 'Rejeté'
    };
    return labels[status] || status;
}

function getAttendanceStatusLabel(status) {
    const labels = {
        'present': 'Présent',
        'absent': 'Absent',
        'late': 'En Retard',
        'half-day': 'Demi-journée'
    };
    return labels[status] || status;
}

// ===========================
// Téléchargement du profil employé en PDF
// ===========================
async function downloadEmployeeProfile(employeeId) {
    // Trouver l'employé dans les données locales
    const employee = AppState.employees.find(e => e.id === employeeId);

    if (!employee) {
        alert('Employé non trouvé');
        return;
    }

    // Récupérer les données complètes de l'employé depuis l'API
    try {
        const fullEmployee = await apiGet(API_ENDPOINTS.EMPLOYEE_DETAIL(employeeId));
        if (fullEmployee) {
            await generateEmployeePDF(fullEmployee);
        } else {
            // Utiliser les données locales si l'API échoue
            await generateEmployeePDF(employee);
        }
    } catch (error) {
        console.error('Erreur:', error);
        // Utiliser les données locales si l'API échoue
        await generateEmployeePDF(employee);
    }
}

async function generateEmployeePDF(employee) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    const pageWidth = 210;
    const marginL = 10;
    const contentW = 190;
    let y = 10;
    const rowH = 10;

    // Couleurs CNPS
    const green = [56, 118, 29];
    const valueColor = [56, 142, 60];
    const border = [180, 180, 180];
    const black = [0, 0, 0];

    // Fonctions utilitaires locales
    function calculateAge(birthDate) {
        if (!birthDate) return null;
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const m = today.getMonth() - birth.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
        return age;
    }

    function calculateRetirementYear(birthDate) {
        if (!birthDate) return null;
        return new Date(birthDate).getFullYear() + 60;
    }

    function calcRetirementDate(bd) {
        if (!bd) return '-';
        const b = new Date(bd);
        const r = new Date(b);
        r.setFullYear(r.getFullYear() + 60);
        return r.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    }

    function formatDatePDF(dateStr) {
        if (!dateStr) return '-';
        return new Date(dateStr).toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    }

    function formatCurrency(amount) {
        if (!amount) return '-';
        return new Intl.NumberFormat('fr-FR').format(amount) + ' FCFA';
    }

    function getMaritalStatusLabel(status) {
        const labels = { 'single': 'Célibataire', 'married': 'Marié(e)', 'divorced': 'Divorcé(e)', 'widowed': 'Veuf/Veuve' };
        return labels[status] || status || '-';
    }

    function getGenderLabel(gender) {
        const labels = { 'male': 'Masculin', 'female': 'Féminin' };
        return labels[gender] || gender || '-';
    }

    function getEmployeeStatusLabel(status) {
        const labels = { 'active': 'Présent et Payé', 'inactive': 'Absent', 'on_leave': 'En Congé' };
        return labels[status] || status || '-';
    }

    function loadImageAsBase64PDF(url) {
        return new Promise((resolve) => {
            const img = new Image();
            img.crossOrigin = 'Anonymous';
            img.onload = function() {
                try {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    canvas.getContext('2d').drawImage(img, 0, 0);
                    resolve(canvas.toDataURL('image/jpeg', 0.8));
                } catch (e) { resolve(null); }
            };
            img.onerror = function() { resolve(null); };
            const sep = url.includes('?') ? '&' : '?';
            img.src = url + sep + 't=' + Date.now();
        });
    }

    // Nettoyage des caractères spéciaux pour jsPDF
    function clean(str) {
        return String(str || '-').replace(/[\u00A0\u202F\u2009\u200B]/g, ' ');
    }

    // === Fonctions de dessin ===
    function drawSectionHeader(title) {
        if (y > 270) { doc.addPage(); y = 10; }
        doc.setFillColor(...green);
        doc.rect(marginL, y, contentW, 12, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('  ' + title, marginL + 3, y + 8.5);
        y += 12;
    }

    function drawInfoRow(label, value, labelW, totalW) {
        if (y > 280) { doc.addPage(); y = 10; }
        doc.setDrawColor(...border);
        doc.setLineWidth(0.3);
        doc.rect(marginL, y, labelW, rowH);
        doc.setTextColor(...black);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(label + ' :', marginL + 3, y + 7);
        doc.rect(marginL + labelW, y, totalW - labelW, rowH);
        doc.setTextColor(...valueColor);
        doc.setFont('helvetica', 'normal');
        doc.text(clean(value).toUpperCase(), marginL + labelW + 3, y + 7);
        y += rowH;
    }

    function fitValue(text, maxW) {
        doc.setFontSize(10);
        if (doc.getTextWidth(text) <= maxW) return;
        doc.setFontSize(8);
        if (doc.getTextWidth(text) <= maxW) return;
        doc.setFontSize(7);
    }

    function drawOneColRow(label, value) {
        if (y > 280) { doc.addPage(); y = 10; }
        const lw = 45;
        const maxValW = contentW - lw - 3;
        doc.setDrawColor(...border);
        doc.setLineWidth(0.3);
        doc.rect(marginL, y, contentW, rowH);
        doc.setTextColor(...black);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(label + ' :', marginL + 3, y + 7);
        doc.setTextColor(...valueColor);
        doc.setFont('helvetica', 'normal');
        let v = clean(value).toUpperCase();
        fitValue(v, maxValW);
        doc.text(v, marginL + lw, y + 7, { maxWidth: maxValW });
        doc.setFontSize(10);
        y += rowH;
    }

    function drawTwoColRow(label1, value1, label2, value2) {
        if (y > 280) { doc.addPage(); y = 10; }
        const halfW = contentW / 2;
        const lw = 45;
        const maxValW = halfW - lw - 3;
        doc.setDrawColor(...border);
        doc.setLineWidth(0.3);

        doc.rect(marginL, y, halfW, rowH);
        doc.setTextColor(...black);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(label1 + ' :', marginL + 3, y + 7);
        doc.setTextColor(...valueColor);
        doc.setFont('helvetica', 'normal');
        let v1 = clean(value1).toUpperCase();
        fitValue(v1, maxValW);
        doc.text(v1, marginL + lw, y + 7, { maxWidth: maxValW });
        doc.setFontSize(10);

        doc.rect(marginL + halfW, y, halfW, rowH);
        if (label2) {
            doc.setTextColor(...black);
            doc.setFont('helvetica', 'bold');
            doc.text(label2 + ' :', marginL + halfW + 3, y + 7);
            doc.setTextColor(...valueColor);
            doc.setFont('helvetica', 'normal');
            let v2 = clean(value2).toUpperCase();
            fitValue(v2, maxValW);
            doc.text(v2, marginL + halfW + lw, y + 7, { maxWidth: maxValW });
            doc.setFontSize(10);
        } else {
            doc.setTextColor(...valueColor);
            doc.text('-', marginL + halfW + 3, y + 7);
        }
        y += rowH;
    }

    // === INFORMATIONS GÉNÉRALES ===
    drawSectionHeader('INFORMATIONS GÉNÉRALES');

    const infoLabelW = 48;
    const infoTotalW = 120;
    const photoAreaX = marginL + infoTotalW;
    const photoAreaW = contentW - infoTotalW;
    const infoStartY = y;

    const matricule = employee.matricule || '-';
    const fullName = `${employee.first_name || ''} ${employee.last_name || ''}`.trim();
    const birthDate = employee.birth_date || employee.birthDate;
    const age = calculateAge(birthDate);
    const retirementYear = calculateRetirementYear(birthDate);

    drawInfoRow('Matricule', matricule, infoLabelW, infoTotalW);
    drawInfoRow('Nom et Prénoms', fullName, infoLabelW, infoTotalW);
    drawInfoRow('Date de Naissance', formatDatePDF(birthDate), infoLabelW, infoTotalW);
    drawInfoRow('Lieu de Naissance', employee.birth_place || '-', infoLabelW, infoTotalW);
    drawInfoRow('Âge actuel', age ? `${age} ans` : '-', infoLabelW, infoTotalW);
    drawInfoRow('Année de Retraite', retirementYear || '-', infoLabelW, infoTotalW);

    // Zone photo (côté droit)
    const infoEndY = y;
    doc.setDrawColor(...border);
    doc.setLineWidth(0.3);
    doc.rect(photoAreaX, infoStartY, photoAreaW, infoEndY - infoStartY);

    if (employee.photo) {
        try {
            const imgData = await loadImageAsBase64PDF(employee.photo);
            if (imgData) {
                const photoW = 35;
                const photoH = 40;
                const photoX = photoAreaX + (photoAreaW - photoW) / 2;
                const photoY = infoStartY + 2;
                doc.addImage(imgData, 'JPEG', photoX, photoY, photoW, photoH);
                doc.setTextColor(...black);
                doc.setFontSize(9);
                doc.setFont('helvetica', 'bold');
                doc.text(String(matricule), photoAreaX + photoAreaW / 2, infoEndY - 2, { align: 'center' });
            }
        } catch (e) {
            console.error('Erreur chargement photo:', e);
        }
    }

    y += 5;

    // === Détails personnels (deux colonnes) ===
    drawTwoColRow('Sexe', getGenderLabel(employee.gender), 'Email', employee.email);
    drawTwoColRow('Numéro CNPS', employee.cnps, 'Commune', employee.commune);
    drawTwoColRow('Téléphone', employee.phone, "Nombre d'enfant", employee.number_of_children);
    drawTwoColRow('Ville', employee.city, null, null);
    drawTwoColRow('Situation Famille', getMaritalStatusLabel(employee.marital_status || employee.maritalStatus), null, null);

    y += 5;

    // === EMPLOI ===
    drawSectionHeader('EMPLOI');
    const deptName = employee.department_name || employee.department;
    drawTwoColRow('Entreprise', deptName, "Date d'embauche", formatDatePDF(employee.hire_date || employee.hireDate));
    drawOneColRow('Direction', employee.direction);
    drawTwoColRow('Salaire', formatCurrency(employee.salary), 'Lieu de Travail', employee.city);
    drawTwoColRow('Emploi', employee.position, null, null);

    y += 5;

    // === ETAT AGENT ===
    drawSectionHeader('ETAT AGENT');
    drawTwoColRow('Date prise de service', formatDatePDF(employee.hire_date || employee.hireDate), 'Solde Congés', (employee.leave_balance != null ? employee.leave_balance : 15) + ' jours');
    drawTwoColRow('Date départ retraite', calcRetirementDate(birthDate), 'Congés Pris', (employee.leaves_taken_this_year || 0) + ' jours');
    drawTwoColRow('Etat', getEmployeeStatusLabel(employee.status), null, null);

    // Télécharger
    const firstName = employee.first_name || employee.firstName || 'Employe';
    const lastName = employee.last_name || employee.lastName || '';
    doc.save(`Fiche_${firstName}_${lastName}.pdf`);
}

// ===========================
// Téléchargement des rapports Excel
// ===========================
async function downloadReport(type) {
    const endpoints = {
        'attendance': API_ENDPOINTS.REPORT_ATTENDANCE,
        'leaves': API_ENDPOINTS.REPORT_LEAVES,
        'departments': API_ENDPOINTS.REPORT_DEPARTMENTS,
        'complete': API_ENDPOINTS.REPORT_COMPLETE,
    };

    const labels = {
        'attendance': 'Rapport de Présence',
        'leaves': 'Rapport des Congés',
        'departments': 'Rapport par Entreprise',
        'complete': 'Rapport RH Complet',
    };

    const url = endpoints[type];
    if (!url) {
        alert('Type de rapport inconnu');
        return;
    }

    // Feedback visuel : changer le bouton
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Génération...';
    btn.disabled = true;

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(url, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
            }
        });

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}`);
        }

        // Récupérer le blob et déclencher le téléchargement
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;

        // Extraire le nom du fichier du header Content-Disposition
        const disposition = response.headers.get('Content-Disposition');
        let filename = `${labels[type]}.xlsx`;
        if (disposition) {
            const match = disposition.match(/filename="?(.+?)"?$/);
            if (match) filename = match[1];
        }

        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);

        // Feedback succès
        btn.innerHTML = '<i class="fas fa-check"></i> Téléchargé !';
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }, 2000);

    } catch (error) {
        console.error('Erreur téléchargement rapport:', error);
        alert(`Erreur lors du téléchargement du ${labels[type]}`);
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// Exposer les fonctions globalement pour les événements onclick
window.editEmployee = editEmployee;
window.deleteEmployee = deleteEmployee;
window.editDepartment = editDepartment;
window.deleteDepartment = deleteDepartment;
window.approveLeave = approveLeave;
window.rejectLeave = rejectLeave;
window.deleteLeave = deleteLeave;
window.closeModal = closeModal;
window.openEmployeeModal = openEmployeeModal;
window.openDepartmentModal = openDepartmentModal;
window.switchAccount = switchAccount;
window.confirmLogout = confirmLogout;
window.downloadEmployeeProfile = downloadEmployeeProfile;
window.downloadReport = downloadReport;
