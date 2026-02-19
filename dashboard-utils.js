/**
 * @fileoverview Fonctions utilitaires partagées par tous les modules du tableau de bord.
 *
 * Ce module fournit :
 *  - escapeHtml  : protection XSS pour toute insertion dans innerHTML
 *  - formatDate  : formatage des dates en français
 *  - getXxxLabel : traduction des codes internes en libellés lisibles
 *  - closeModal  : fermeture générique des fenêtres modales
 *  - downloadReport : téléchargement asynchrone des rapports Excel
 *
 * Toutes les fonctions sont exposées sur `window` pour être accessibles
 * depuis les gestionnaires d'événements inline des autres modules.
 */

// ===========================
// Sécurité — Anti-XSS
// ===========================

/**
 * Échappe les caractères HTML spéciaux pour prévenir les injections XSS
 * lors de l'insertion de données utilisateur dans innerHTML.
 *
 * Remplace : & < > " '  par leurs entités HTML équivalentes.
 *
 * @param {*} str - Valeur à échapper (sera convertie en chaîne).
 *                  null et undefined retournent une chaîne vide.
 * @returns {string} Chaîne sécurisée pour insertion dans innerHTML.
 *
 * @example
 * escapeHtml('<script>alert(1)</script>')
 * // → '&lt;script&gt;alert(1)&lt;/script&gt;'
 */
function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// ===========================
// Interface utilisateur
// ===========================

/**
 * Ferme une fenêtre modale en retirant la classe CSS `active`.
 *
 * @param {string} modalId - L'identifiant (`id`) de l'élément modal à fermer.
 * @returns {void}
 */
function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// ===========================
// Formatage
// ===========================

/**
 * Formate une chaîne de date ISO en date lisible en français (JJ/MM/AAAA).
 *
 * @param {string|null} dateString - Chaîne de date au format ISO 8601 (ex. "2024-03-15").
 * @returns {string} Date formatée (ex. "15/03/2024"), ou '-' si la valeur est falsy.
 *
 * @example
 * formatDate('2024-03-15') // → '15/03/2024'
 * formatDate(null)         // → '-'
 */
function formatDate(dateString) {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

// ===========================
// Traduction des codes internes
// ===========================

/**
 * Retourne le libellé français d'un statut d'employé.
 *
 * @param {string} status - Code interne : 'active' | 'inactive' | 'on_leave' | 'pending'.
 * @returns {string} Libellé lisible, ou le code brut si inconnu.
 */
function getStatusLabel(status) {
    const labels = {
        'active': 'Actif',
        'inactive': 'Inactif',
        'on_leave': 'En congé',
        'pending': 'En attente'
    };
    return labels[status] || status;
}

/**
 * Retourne le libellé français d'un type de congé.
 *
 * @param {string} type - Code interne : 'paid' | 'sick' | 'unpaid' | 'parental' | 'other'.
 * @returns {string} Libellé lisible, ou le code brut si inconnu.
 */
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

/**
 * Retourne le libellé français d'un statut de demande de congé.
 *
 * @param {string} status - Code interne : 'pending' | 'manager_approved' | 'approved' | 'rejected'.
 * @returns {string} Libellé lisible, ou le code brut si inconnu.
 */
function getLeaveStatusLabel(status) {
    const labels = {
        'pending': 'En attente',
        'manager_approved': 'Validé Manager',
        'approved': 'Approuvé',
        'rejected': 'Rejeté'
    };
    return labels[status] || status;
}

/**
 * Retourne le libellé français d'un statut de présence.
 *
 * @param {string} status - Code interne : 'present' | 'absent' | 'late' | 'half-day'.
 * @returns {string} Libellé lisible, ou le code brut si inconnu.
 */
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
// Téléchargement des rapports Excel
// ===========================

/**
 * Télécharge un rapport Excel depuis l'API et déclenche le téléchargement navigateur.
 *
 * La fonction :
 *  1. Envoie une requête GET authentifiée (JWT) vers l'endpoint correspondant au type.
 *  2. Convertit la réponse en Blob et crée un lien de téléchargement temporaire.
 *  3. Lit le nom du fichier depuis l'en-tête `Content-Disposition` si disponible.
 *  4. Gère l'état visuel du bouton (spinner → succès → retour à l'état initial).
 *
 * @param {string} type - Type de rapport : 'attendance' | 'leaves' | 'departments' | 'complete'.
 * @returns {Promise<void>}
 *
 * @example
 * // Appelée depuis un bouton HTML :
 * // <button onclick="downloadReport('attendance')">Télécharger</button>
 */
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

    // Désactiver le bouton pendant la génération
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Génération...';
    btn.disabled = true;

    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch(url, {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            throw new Error(`Erreur ${response.status}`);
        }

        // Créer un lien temporaire pour déclencher le téléchargement
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;

        // Lire le nom du fichier depuis l'en-tête HTTP si fourni
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

        // Feedback visuel de succès, puis rétablissement du bouton
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

// ===========================
// Exports globaux
// ===========================
window.escapeHtml = escapeHtml;
window.closeModal = closeModal;
window.downloadReport = downloadReport;
