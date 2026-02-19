/**
 * @fileoverview Module de gestion des demandes de congés du tableau de bord.
 *
 * Responsabilités :
 *  - Affichage du tableau des congés avec filtrage par statut (onglets)
 *  - Actions différenciées selon le rôle : Approuver / Valider / Rejeter
 *  - Ouverture du modal de demande de congé
 *  - Soumission, approbation, rejet et suppression via API REST
 *
 * Flux d'approbation à deux niveaux :
 *  1. Le manager valide (status → 'manager_approved')
 *  2. L'entreprise approuve définitivement (status → 'approved')
 *  L'admin peut approuver directement (court-circuit des deux étapes).
 *
 * Ce module dépend de :
 *  - AppState, API_ENDPOINTS, apiPost/apiDelete (dashboard.js)
 *  - escapeHtml (dashboard-utils.js)
 *  - formatDate, getLeaveTypeLabel, getLeaveStatusLabel (dashboard-utils.js)
 */

// ===========================
// Affichage du tableau
// ===========================

/**
 * Rend le tableau HTML des demandes de congé, filtrées par statut.
 *
 * Les boutons d'action affichés dépendent du rôle de l'utilisateur connecté
 * (AppState.currentUser.role) et du statut actuel de chaque demande.
 * Les données texte issues de l'API (noms, raisons) sont échappées via escapeHtml().
 *
 * @param {string} [filter='all'] - Filtre de statut à appliquer :
 *   'all' | 'pending' | 'manager_approved' | 'approved' | 'rejected'.
 * @returns {void}
 */
function renderLeavesTable(filter = 'all') {
    let filteredLeaves = AppState.leaves;

    if (filter !== 'all') {
        filteredLeaves = AppState.leaves.filter(l => l.status === filter);
    }

    const role = AppState.currentUser ? AppState.currentUser.role : '';

    const tbody = document.getElementById('leavesTableBody');
    tbody.innerHTML = filteredLeaves.map(leave => {
        // Construction des boutons d'action selon le rôle et le statut
        let actionButtons = '';

        if (role === 'admin') {
            // L'admin peut approuver les congés en attente ou validés par manager
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
            // Le manager effectue la première validation (pending → manager_approved)
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
                // L'entreprise doit attendre la validation du manager
                actionButtons += `
                    <span class="action-info"><i class="fas fa-hourglass-half"></i> En attente du Manager</span>`;
            } else if (leave.status === 'manager_approved') {
                // L'entreprise peut approuver ou rejeter après validation manager
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
            <td>${escapeHtml(leave.employeeName)}</td>
            <td>${getLeaveTypeLabel(leave.type)}</td>
            <td>${formatDate(leave.startDate)}</td>
            <td>${formatDate(leave.endDate)}</td>
            <td>${leave.days} jours</td>
            <td>${escapeHtml(leave.reason)}</td>
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

/**
 * Gestionnaire de clic sur un onglet de filtre (Tous / En attente / Approuvé…).
 *
 * Met à jour l'onglet actif visuellement et re-rend le tableau avec le filtre
 * correspondant à l'attribut `data-tab` de l'onglet cliqué.
 *
 * @param {MouseEvent} e - Événement de clic sur le bouton d'onglet.
 * @returns {void}
 */
function handleTabClick(e) {
    const tab = e.target.dataset.tab;

    // Désactiver tous les onglets, puis activer celui cliqué
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    e.target.classList.add('active');

    renderLeavesTable(tab);
}

// ===========================
// Modal de demande de congé
// ===========================

/**
 * Ouvre le modal de demande de congé et peuple la liste des employés.
 *
 * Réinitialise le formulaire avant ouverture pour éviter toute pré-saisie
 * résiduelle d'une ouverture précédente.
 *
 * @returns {void}
 */
function openLeaveModal() {
    const modal = document.getElementById('leaveModal');
    const form = document.getElementById('leaveForm');
    const empSelect = document.getElementById('leaveEmployee');

    // Peupler la liste des employés disponibles
    empSelect.innerHTML = '<option value="">Sélectionner...</option>' +
        AppState.employees.map(emp =>
            `<option value="${emp.id}">${escapeHtml(emp.firstName)} ${escapeHtml(emp.lastName)}</option>`
        ).join('');

    form.reset();
    modal.classList.add('active');
}

// ===========================
// CRUD via API
// ===========================

/**
 * Gère la soumission du formulaire de demande de congé.
 *
 * Envoie un POST vers API_ENDPOINTS.LEAVES avec les données du formulaire.
 * Après succès : recharge les données et re-rend le tableau.
 *
 * @param {SubmitEvent} e - Événement de soumission du formulaire.
 * @returns {Promise<void>}
 */
async function handleLeaveSubmit(e) {
    e.preventDefault();

    const employeeId = parseInt(document.getElementById('leaveEmployee').value);
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

/**
 * Approuve ou valide une demande de congé selon le rôle de l'utilisateur.
 *
 * Le comportement côté API dépend du rôle :
 *  - Manager  → status passe à 'manager_approved'
 *  - Entreprise → status passe à 'approved' (requiert manager_approved au préalable)
 *  - Admin    → approbation directe en 'approved'
 *
 * @param {number} id - Identifiant de la demande de congé à approuver.
 * @returns {Promise<void>}
 */
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

/**
 * Rejette une demande de congé (statut → 'rejected').
 *
 * Seuls les utilisateurs avec le droit is_staff ou is_superuser
 * peuvent rejeter (contrôle effectué côté serveur).
 *
 * @param {number} id - Identifiant de la demande de congé à rejeter.
 * @returns {Promise<void>}
 */
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

/**
 * Supprime une demande de congé après confirmation de l'utilisateur.
 *
 * Note : l'API refuse la suppression des congés déjà approuvés (HTTP 400).
 *
 * @param {number} id - Identifiant de la demande de congé à supprimer.
 * @returns {Promise<void>}
 */
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
// Exports globaux
// ===========================
window.approveLeave = approveLeave;
window.rejectLeave = rejectLeave;
window.deleteLeave = deleteLeave;
