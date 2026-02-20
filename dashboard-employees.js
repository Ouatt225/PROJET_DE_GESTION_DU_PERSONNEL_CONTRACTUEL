/**
 * @fileoverview Module de gestion des employés du tableau de bord.
 *
 * Responsabilités :
 *  - Affichage et filtrage du tableau des employés (renderEmployeesTable)
 *  - Peuplement dynamique des listes déroulantes (entreprises, postes)
 *  - Ouverture du modal en mode création ou édition (openEmployeeModal)
 *  - Soumission du formulaire (création / modification via API REST)
 *  - Suppression d'un employé avec confirmation
 *
 * Ce module dépend de :
 *  - AppState        (dashboard.js) : état global de l'application
 *  - API_ENDPOINTS   (dashboard.js) : URLs de l'API
 *  - apiGet/apiPost/apiPut/apiDelete (dashboard.js) : wrappers fetch authentifiés
 *  - escapeHtml      (dashboard-utils.js) : protection XSS
 *  - formatDate, getStatusLabel (dashboard-utils.js) : formatage
 */

// ===========================
// Affichage du tableau
// ===========================

/**
 * Rend le tableau HTML des employés en appliquant les filtres actifs
 * (recherche textuelle, entreprise, poste).
 *
 * Lit les valeurs courantes des champs #searchEmployee, #filterDepartment
 * et #filterPosition avant de filtrer AppState.employees.
 * Tous les champs texte provenant de l'API sont échappés via escapeHtml()
 * pour prévenir les injections XSS.
 *
 * @returns {void}
 */
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

    const role = AppState.currentUser?.role;
    const canEditDelete = role === 'admin';

    const tbody = document.getElementById('employeesTableBody');
    tbody.innerHTML = filteredEmployees.map(emp => `
        <tr>
            <td>#${emp.id}</td>
            <td>${escapeHtml(emp.firstName)} ${escapeHtml(emp.lastName)}</td>
            <td>${escapeHtml(emp.email)}</td>
            <td>${escapeHtml(emp.department)}</td>
            <td>${escapeHtml(emp.position)}</td>
            <td>${formatDate(emp.hireDate)}</td>
            <td><span class="status-badge status-${emp.status}">${getStatusLabel(emp.status)}</span></td>
            <td>
                <div class="action-buttons">
                    <button class="action-btn download" onclick="downloadEmployeeProfile(${emp.id})" title="Télécharger le profil">
                        <i class="fas fa-download"></i>
                    </button>
                    ${canEditDelete ? `
                    <button class="action-btn edit" onclick="editEmployee(${emp.id})">
                        <i class="fas fa-edit"></i> Modifier
                    </button>
                    <button class="action-btn delete" onclick="deleteEmployee(${emp.id})">
                        <i class="fas fa-trash"></i> Supprimer
                    </button>` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

/**
 * Gestionnaire de l'événement `input` sur le champ de recherche.
 * Déclenche un re-rendu du tableau avec le nouveau terme de recherche.
 *
 * @returns {void}
 */
function handleEmployeeSearch() {
    renderEmployeesTable();
}

// ===========================
// Filtres et listes déroulantes
// ===========================

/**
 * Peuple les listes déroulantes de filtre par entreprise et par poste,
 * ainsi que le sélecteur d'entreprise dans le modal d'ajout d'employé.
 *
 * Sources :
 *  - AppState.departments → #filterDepartment, #empDepartment
 *  - AppState.employees   → #filterPosition  (valeurs uniques des postes)
 *
 * @returns {void}
 */
function populateDepartmentFilters() {
    const deptSelect = document.getElementById('filterDepartment');
    const empDeptSelect = document.getElementById('empDepartment');

    const deptOptions = AppState.departments.map(dept =>
        `<option value="${escapeHtml(dept.name)}">${escapeHtml(dept.name)}</option>`
    ).join('');

    if (deptSelect) {
        deptSelect.innerHTML = '<option value="">Tous les entreprises</option>' + deptOptions;
    }
    if (empDeptSelect) {
        empDeptSelect.innerHTML = '<option value="">Sélectionner...</option>' + deptOptions;
    }

    // Dédupliquer les postes présents dans AppState
    const positions = [...new Set(AppState.employees.map(e => e.position))];
    const posSelect = document.getElementById('filterPosition');
    if (posSelect) {
        posSelect.innerHTML = '<option value="">Tous les postes</option>' +
            positions.map(pos => `<option value="${escapeHtml(pos)}">${escapeHtml(pos)}</option>`).join('');
    }
}

// ===========================
// Modal employé (création / édition)
// ===========================

/**
 * Ouvre le modal de saisie employé en mode création ou édition.
 *
 * En mode édition (employeeId fourni) :
 *  - Remplit tous les champs du formulaire avec les données de l'employé.
 *  - Met à jour le titre du modal.
 *
 * En mode création (employeeId omis ou null) :
 *  - Réinitialise le formulaire.
 *  - Met à jour le titre du modal.
 *
 * Appelle populateDepartmentFilters() avant d'afficher le modal pour
 * s'assurer que les listes déroulantes sont à jour.
 *
 * @param {number|null} [employeeId=null] - ID de l'employé à modifier,
 *   ou null pour une création.
 * @returns {void}
 */
function openEmployeeModal(employeeId = null) {
    populateDepartmentFilters();

    const modal = document.getElementById('employeeModal');
    const form = document.getElementById('employeeForm');
    const title = document.getElementById('employeeModalTitle');

    if (employeeId) {
        // Mode édition : pré-remplir le formulaire
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
        // Mode création : formulaire vierge
        title.textContent = 'Ajouter un Employé';
        form.reset();
        document.getElementById('empId').value = '';
    }

    modal.classList.add('active');
}

// ===========================
// CRUD via API
// ===========================

/**
 * Gère la soumission du formulaire employé.
 *
 * Selon la présence de la valeur dans #empId :
 *  - PUT  vers EMPLOYEE_DETAIL(id) si édition.
 *  - POST vers EMPLOYEES si création.
 *
 * Après succès : recharge les données, re-rend le tableau et ferme le modal.
 *
 * @param {SubmitEvent} e - Événement de soumission du formulaire.
 * @returns {Promise<void>}
 */
async function handleEmployeeSubmit(e) {
    e.preventDefault();

    const id = document.getElementById('empId').value;
    const departmentName = document.getElementById('empDepartment').value;
    const department = AppState.departments.find(d => d.name === departmentName);
    const departmentId = department ? department.id : null;

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
            result = await apiPut(API_ENDPOINTS.EMPLOYEE_DETAIL(id), employeeData);
        } else {
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

/**
 * Ouvre le modal en mode édition pour l'employé dont l'identifiant est donné.
 * Alias de openEmployeeModal(id) utilisé par les boutons onclick inline.
 *
 * @param {number} id - Identifiant de l'employé à modifier.
 * @returns {void}
 */
function editEmployee(id) {
    openEmployeeModal(id);
}

/**
 * Supprime un employé après confirmation de l'utilisateur.
 *
 * Envoie une requête DELETE vers EMPLOYEE_DETAIL(id).
 * Après succès : recharge les données et re-rend le tableau.
 *
 * @param {number} id - Identifiant de l'employé à supprimer.
 * @returns {Promise<void>}
 */
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
// Exports globaux
// ===========================
window.editEmployee = editEmployee;
window.deleteEmployee = deleteEmployee;
window.openEmployeeModal = openEmployeeModal;
