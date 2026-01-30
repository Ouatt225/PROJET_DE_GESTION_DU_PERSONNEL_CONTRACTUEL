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

// ===========================
// Données de Démonstration
// ===========================
const DEMO_USERS = {
    admin: { username: 'admin', password: 'admin123', role: 'admin', name: 'Administrateur' },
    manager: { username: 'manager', password: 'manager123', role: 'manager', name: 'Manager' },
    employee: { username: 'employee', password: 'employee123', role: 'employee', name: 'Employé' }
};

// Départements par défaut
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
    initializeApp();
    setupEventListeners();
});

function initializeApp() {
    // Charger les données depuis localStorage ou utiliser les données par défaut
    AppState.departments = JSON.parse(localStorage.getItem('departments')) || DEFAULT_DEPARTMENTS;
    AppState.employees = JSON.parse(localStorage.getItem('employees')) || DEFAULT_EMPLOYEES;
    AppState.leaves = JSON.parse(localStorage.getItem('leaves')) || DEFAULT_LEAVES;
    AppState.attendance = JSON.parse(localStorage.getItem('attendance')) || DEFAULT_ATTENDANCE;

    // Sauvegarder les données par défaut si aucune donnée n'existe
    saveToLocalStorage();
}

function saveToLocalStorage() {
    localStorage.setItem('departments', JSON.stringify(AppState.departments));
    localStorage.setItem('employees', JSON.stringify(AppState.employees));
    localStorage.setItem('leaves', JSON.stringify(AppState.leaves));
    localStorage.setItem('attendance', JSON.stringify(AppState.attendance));
}

// ===========================
// Gestion des Événements
// ===========================
function setupEventListeners() {
    // Connexion
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
    }

    // Déconnexion
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('submit', handleLogout);
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
function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('userRole').value;

    // Vérification des identifiants
    const user = DEMO_USERS[username];

    if (user && user.password === password && user.role === role) {
        AppState.currentUser = user;

        // Afficher le dashboard
        document.getElementById('loginPage').classList.remove('active');
        document.getElementById('dashboardPage').classList.add('active');

        // Mettre à jour les informations utilisateur
        document.getElementById('currentUserName').textContent = user.name;
        document.getElementById('currentUserRole').textContent = getRoleLabel(user.role);

        // Initialiser le dashboard
        renderDashboard();
        applyRolePermissions();
    } else {
        alert('Identifiants incorrects. Veuillez réessayer.');
    }
}

function handleLogout() {
    AppState.currentUser = null;
    document.getElementById('dashboardPage').classList.remove('active');
    document.getElementById('loginPage').classList.add('active');
    document.getElementById('loginForm').reset();
}

function getRoleLabel(role) {
    const labels = {
        'admin': 'Administrateur',
        'manager': 'Manager',
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
    const pendingLeaves = AppState.leaves.filter(l => l.status === 'pending').slice(0, 5);

    const container = document.getElementById('pendingLeaves');
    container.innerHTML = pendingLeaves.map(leave => `
        <div class="list-item">
            <div class="list-item-avatar">
                <i class="fas fa-calendar-alt"></i>
            </div>
            <div class="list-item-info">
                <div class="name">${leave.employeeName}</div>
                <div class="detail">${formatDate(leave.startDate)} - ${formatDate(leave.endDate)} (${leave.days} jours)</div>
            </div>
            <span class="status-badge status-${leave.status}">En attente</span>
        </div>
    `).join('');
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
        deptSelect.innerHTML = '<option value="">Tous les départements</option>' + deptOptions;
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
        document.getElementById('empAddress').value = employee.address;
    } else {
        title.textContent = 'Ajouter un Employé';
        form.reset();
        document.getElementById('empId').value = '';
    }

    modal.classList.add('active');
}

function handleEmployeeSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('empId').value;
    const employee = {
        id: id ? parseInt(id) : Date.now(),
        firstName: document.getElementById('empFirstName').value,
        lastName: document.getElementById('empLastName').value,
        email: document.getElementById('empEmail').value,
        phone: document.getElementById('empPhone').value,
        department: document.getElementById('empDepartment').value,
        position: document.getElementById('empPosition').value,
        hireDate: document.getElementById('empHireDate').value,
        salary: parseFloat(document.getElementById('empSalary').value) || 0,
        address: document.getElementById('empAddress').value,
        status: 'active'
    };

    if (id) {
        // Modifier
        const index = AppState.employees.findIndex(e => e.id === parseInt(id));
        AppState.employees[index] = employee;
    } else {
        // Ajouter
        AppState.employees.push(employee);
    }

    saveToLocalStorage();
    renderEmployeesTable();
    closeModal('employeeModal');

    alert('Employé enregistré avec succès !');
}

function editEmployee(id) {
    openEmployeeModal(id);
}

function deleteEmployee(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cet employé ?')) {
        AppState.employees = AppState.employees.filter(e => e.id !== id);
        saveToLocalStorage();
        renderEmployeesTable();
        alert('Employé supprimé avec succès !');
    }
}

// ===========================
// Gestion des Départements
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
        title.textContent = 'Modifier un Département';

        document.getElementById('deptId').value = dept.id;
        document.getElementById('deptName').value = dept.name;
        document.getElementById('deptManager').value = dept.manager;
        document.getElementById('deptDescription').value = dept.description;
    } else {
        title.textContent = 'Ajouter un Département';
        form.reset();
        document.getElementById('deptId').value = '';
    }

    modal.classList.add('active');
}

function handleDepartmentSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('deptId').value;
    const department = {
        id: id ? parseInt(id) : Date.now(),
        name: document.getElementById('deptName').value,
        manager: document.getElementById('deptManager').value,
        description: document.getElementById('deptDescription').value
    };

    if (id) {
        const index = AppState.departments.findIndex(d => d.id === parseInt(id));
        AppState.departments[index] = department;
    } else {
        AppState.departments.push(department);
    }

    saveToLocalStorage();
    renderDepartmentsGrid();
    populateDepartmentFilters();
    closeModal('departmentModal');

    alert('Département enregistré avec succès !');
}

function editDepartment(id) {
    openDepartmentModal(id);
}

function deleteDepartment(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer ce département ?')) {
        AppState.departments = AppState.departments.filter(d => d.id !== id);
        saveToLocalStorage();
        renderDepartmentsGrid();
        alert('Département supprimé avec succès !');
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

    const tbody = document.getElementById('leavesTableBody');
    tbody.innerHTML = filteredLeaves.map(leave => `
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
                    ${leave.status === 'pending' ? `
                        <button class="action-btn approve" onclick="approveLeave(${leave.id})">
                            <i class="fas fa-check"></i> Approuver
                        </button>
                        <button class="action-btn reject" onclick="rejectLeave(${leave.id})">
                            <i class="fas fa-times"></i> Rejeter
                        </button>
                    ` : ''}
                    <button class="action-btn delete" onclick="deleteLeave(${leave.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        </tr>
    `).join('');
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

function handleLeaveSubmit(e) {
    e.preventDefault();

    const employeeId = parseInt(document.getElementById('leaveEmployee').value);
    const employee = AppState.employees.find(e => e.id === employeeId);

    const startDate = new Date(document.getElementById('leaveStartDate').value);
    const endDate = new Date(document.getElementById('leaveEndDate').value);
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;

    const leave = {
        id: Date.now(),
        employeeId: employeeId,
        employeeName: `${employee.firstName} ${employee.lastName}`,
        type: document.getElementById('leaveType').value,
        startDate: document.getElementById('leaveStartDate').value,
        endDate: document.getElementById('leaveEndDate').value,
        days: days,
        reason: document.getElementById('leaveReason').value,
        status: 'pending'
    };

    AppState.leaves.push(leave);
    saveToLocalStorage();
    renderLeavesTable();
    closeModal('leaveModal');

    alert('Demande de congé soumise avec succès !');
}

function approveLeave(id) {
    const leave = AppState.leaves.find(l => l.id === id);
    leave.status = 'approved';
    saveToLocalStorage();
    renderLeavesTable('pending');
    alert('Congé approuvé !');
}

function rejectLeave(id) {
    const leave = AppState.leaves.find(l => l.id === id);
    leave.status = 'rejected';
    saveToLocalStorage();
    renderLeavesTable('pending');
    alert('Congé rejeté !');
}

function deleteLeave(id) {
    if (confirm('Êtes-vous sûr de vouloir supprimer cette demande de congé ?')) {
        AppState.leaves = AppState.leaves.filter(l => l.id !== id);
        saveToLocalStorage();
        renderLeavesTable();
        alert('Demande de congé supprimée !');
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

function handleAttendanceSubmit(e) {
    e.preventDefault();

    const employeeId = parseInt(document.getElementById('attEmployee').value);
    const employee = AppState.employees.find(e => e.id === employeeId);

    const checkIn = document.getElementById('attCheckIn').value;
    const checkOut = document.getElementById('attCheckOut').value;

    let hours = 0;
    if (checkIn && checkOut) {
        const start = new Date(`2000-01-01 ${checkIn}`);
        const end = new Date(`2000-01-01 ${checkOut}`);
        hours = (end - start) / (1000 * 60 * 60);
    }

    const attendance = {
        id: Date.now(),
        employeeId: employeeId,
        employeeName: `${employee.firstName} ${employee.lastName}`,
        date: document.getElementById('attDate').value,
        checkIn: checkIn,
        checkOut: checkOut,
        hours: hours,
        status: document.getElementById('attStatus').value
    };

    AppState.attendance.push(attendance);
    saveToLocalStorage();
    renderAttendanceTable();
    closeModal('attendanceModal');

    alert('Présence enregistrée avec succès !');
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
