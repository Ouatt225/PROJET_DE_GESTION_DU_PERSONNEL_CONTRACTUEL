/**
 * @fileoverview Module de gestion des entreprises (departments) du tableau de bord.
 *
 * Responsabilités :
 *  - Affichage de la grille des cartes entreprises avec statistiques
 *  - Ouverture du modal en mode création ou édition
 *  - Soumission du formulaire (création / modification via API REST)
 *  - Suppression d'une entreprise avec confirmation
 *
 * Note terminologique : dans ce projet, "Department" désigne une entreprise
 * prestataire (ex. AZING, CAFOR…), et non un département interne.
 *
 * Ce module dépend de :
 *  - AppState, API_ENDPOINTS, apiPost/apiPut/apiDelete (dashboard.js)
 *  - escapeHtml (dashboard-utils.js)
 *  - populateDepartmentFilters (dashboard-employees.js)
 */

// ===========================
// Affichage de la grille
// ===========================

/**
 * Rend la grille HTML des cartes entreprises.
 *
 * Chaque carte affiche : nom, description, responsable, nombre d'employés
 * et les boutons Modifier / Supprimer.
 * Le nombre d'employés est calculé localement à partir de AppState.employees.
 * Toutes les données texte issues de l'API sont échappées via escapeHtml().
 *
 * @returns {void}
 */
function renderDepartmentsGrid() {
    const grid = document.getElementById('departmentsGrid');

    grid.innerHTML = AppState.departments.map(dept => {
        // Compter les employés affiliés à cette entreprise depuis l'état local
        const employeeCount = AppState.employees.filter(e => e.department === dept.name).length;

        return `
            <div class="department-card">
                <h3>${escapeHtml(dept.name)}</h3>
                <p>${escapeHtml(dept.description)}</p>
                <div class="department-stats">
                    <div class="department-stat">
                        <div class="label">Responsable</div>
                        <div class="value" style="font-size: 1rem; color: var(--text-primary);">${escapeHtml(dept.manager)}</div>
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

// ===========================
// Modal entreprise (création / édition)
// ===========================

/**
 * Ouvre le modal de saisie d'une entreprise en mode création ou édition.
 *
 * En mode édition (deptId fourni) :
 *  - Remplit les champs #deptId, #deptName, #deptManager, #deptDescription.
 *  - Adapte le titre du modal.
 *
 * En mode création (deptId omis ou null) :
 *  - Réinitialise le formulaire.
 *  - Adapte le titre du modal.
 *
 * @param {number|null} [deptId=null] - Identifiant de l'entreprise à modifier,
 *   ou null pour une création.
 * @returns {void}
 */
function openDepartmentModal(deptId = null) {
    const modal = document.getElementById('departmentModal');
    const form = document.getElementById('departmentForm');
    const title = document.getElementById('departmentModalTitle');

    if (deptId) {
        // Mode édition : pré-remplir le formulaire
        const dept = AppState.departments.find(d => d.id === deptId);
        title.textContent = 'Modifier un Entreprise';

        document.getElementById('deptId').value = dept.id;
        document.getElementById('deptName').value = dept.name;
        document.getElementById('deptManager').value = dept.manager;
        document.getElementById('deptDescription').value = dept.description;
    } else {
        // Mode création : formulaire vierge
        title.textContent = 'Ajouter un Entreprise';
        form.reset();
        document.getElementById('deptId').value = '';
    }

    modal.classList.add('active');
}

// ===========================
// CRUD via API
// ===========================

/**
 * Gère la soumission du formulaire entreprise.
 *
 * Selon la présence de la valeur dans #deptId :
 *  - PUT  vers DEPARTMENT_DETAIL(id) si édition.
 *  - POST vers DEPARTMENTS si création.
 *
 * Après succès : recharge les données, re-rend la grille,
 * met à jour les filtres et ferme le modal.
 *
 * @param {SubmitEvent} e - Événement de soumission du formulaire.
 * @returns {Promise<void>}
 */
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
            result = await apiPut(API_ENDPOINTS.DEPARTMENT_DETAIL(id), departmentData);
        } else {
            result = await apiPost(API_ENDPOINTS.DEPARTMENTS, departmentData);
        }

        if (result.ok) {
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

/**
 * Ouvre le modal en mode édition pour l'entreprise dont l'identifiant est donné.
 * Alias de openDepartmentModal(id) utilisé par les boutons onclick inline.
 *
 * @param {number} id - Identifiant de l'entreprise à modifier.
 * @returns {void}
 */
function editDepartment(id) {
    openDepartmentModal(id);
}

/**
 * Supprime une entreprise après confirmation de l'utilisateur.
 *
 * Envoie une requête DELETE vers DEPARTMENT_DETAIL(id).
 * Après succès : recharge les données et re-rend la grille.
 *
 * @param {number} id - Identifiant de l'entreprise à supprimer.
 * @returns {Promise<void>}
 */
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
// Exports globaux
// ===========================
window.editDepartment = editDepartment;
window.deleteDepartment = deleteDepartment;
window.openDepartmentModal = openDepartmentModal;
