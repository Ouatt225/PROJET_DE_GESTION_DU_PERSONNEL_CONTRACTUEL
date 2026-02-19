/**
 * @fileoverview Module de gestion des présences du tableau de bord.
 *
 * Responsabilités :
 *  - Affichage du tableau des pointages triés par date décroissante
 *  - Placeholder du calendrier mensuel (fonctionnalité à venir)
 *  - Ouverture du modal d'enregistrement d'une présence
 *  - Soumission du formulaire de pointage via API REST
 *
 * Les statuts gérés sont : 'present' | 'absent' | 'late' | 'half-day'.
 * Le calcul des heures travaillées est effectué côté serveur (propriété
 * `hours_worked` du modèle Attendance).
 *
 * Ce module dépend de :
 *  - AppState, API_ENDPOINTS, apiPost (dashboard.js)
 *  - escapeHtml (dashboard-utils.js)
 *  - formatDate, getAttendanceStatusLabel (dashboard-utils.js)
 */

// ===========================
// Affichage du tableau
// ===========================

/**
 * Rend le tableau HTML des enregistrements de présence,
 * triés par date décroissante (le plus récent en premier).
 *
 * Note : AppState.attendance est trié en place. Les données texte
 * provenant de l'API sont échappées via escapeHtml() pour prévenir les XSS.
 * Les champs horaires null sont remplacés par '-'.
 *
 * @returns {void}
 */
function renderAttendanceTable() {
    const tbody = document.getElementById('attendanceTableBody');

    // Tri par date décroissante (modifie AppState.attendance en place)
    const sortedAttendance = AppState.attendance.sort((a, b) =>
        new Date(b.date) - new Date(a.date)
    );

    tbody.innerHTML = sortedAttendance.map(att => `
        <tr>
            <td>${formatDate(att.date)}</td>
            <td>${escapeHtml(att.employeeName)}</td>
            <td>${escapeHtml(att.checkIn) || '-'}</td>
            <td>${escapeHtml(att.checkOut) || '-'}</td>
            <td>${escapeHtml(att.hours) || '-'} heures</td>
            <td><span class="status-badge status-${att.status}">${getAttendanceStatusLabel(att.status)}</span></td>
        </tr>
    `).join('');
}

/**
 * Affiche le calendrier mensuel des présences (placeholder).
 *
 * Le calendrier interactif n'est pas encore implémenté.
 * Cette fonction insère un message informatif dans le conteneur #attendanceCalendar.
 *
 * @returns {void}
 */
function renderAttendanceCalendar() {
    const calendar = document.getElementById('attendanceCalendar');
    calendar.innerHTML = '<p style="text-align: center; padding: 2rem; color: var(--text-secondary);">Calendrier des présences - Fonctionnalité à venir</p>';
}

// ===========================
// Modal d'enregistrement
// ===========================

/**
 * Ouvre le modal de pointage et prépare le formulaire.
 *
 * Peuple la liste des employés (#attEmployee) depuis AppState.employees.
 * Pré-remplit la date (#attDate) avec la date du jour.
 * Réinitialise le reste du formulaire.
 *
 * @returns {void}
 */
function openAttendanceModal() {
    const modal = document.getElementById('attendanceModal');
    const form = document.getElementById('attendanceForm');
    const empSelect = document.getElementById('attEmployee');

    // Peupler la liste des employés
    empSelect.innerHTML = '<option value="">Sélectionner...</option>' +
        AppState.employees.map(emp =>
            `<option value="${emp.id}">${escapeHtml(emp.firstName)} ${escapeHtml(emp.lastName)}</option>`
        ).join('');

    // Pré-saisir la date du jour au format YYYY-MM-DD
    document.getElementById('attDate').value = new Date().toISOString().split('T')[0];

    form.reset();
    modal.classList.add('active');
}

// ===========================
// Création via API
// ===========================

/**
 * Gère la soumission du formulaire de pointage.
 *
 * Construit le payload et envoie un POST vers API_ENDPOINTS.ATTENDANCES.
 * Le calcul des heures travaillées (check_in / check_out) est délégué au serveur.
 * Après succès : recharge les données et re-rend le tableau.
 *
 * @param {SubmitEvent} e - Événement de soumission du formulaire.
 * @returns {Promise<void>}
 */
async function handleAttendanceSubmit(e) {
    e.preventDefault();

    const employeeId = parseInt(document.getElementById('attEmployee').value);
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
