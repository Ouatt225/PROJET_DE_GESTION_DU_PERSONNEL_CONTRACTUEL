/**
 * @fileoverview Système d'alarmes de rappel pour les congés approuvés.
 *
 * Deux alarmes sont générées automatiquement côté backend lorsqu'un congé
 * est approuvé :
 *   - J-7  : 7 jours avant le début du congé (rappel anticipé).
 *   - Veille : la veille du début du congé (rappel de dernière minute).
 *
 * Ce module gère :
 *   - Le polling de l'API toutes les 60 secondes.
 *   - L'affichage du badge (nombre d'alarmes non lues) sur la cloche.
 *   - Le dropdown listant chaque alarme avec les détails du congé.
 *   - Le marquage comme "lu" (par alarme ou en masse).
 *   - Un toast de notification lors de l'apparition d'une nouvelle alarme.
 *
 * Rôles concernés : admin, manager, entreprise (pas les employés).
 */

// ===========================
// État local des notifications
// ===========================

const NotifState = {
    /** @type {Object[]} */
    notifications: [],
    /** @type {number} */
    unreadCount: 0,
    /** @type {number|null} ID du setInterval */
    pollInterval: null,
    /** Ensemble des IDs déjà vus (pour détecter les nouvelles alarmes) */
    seenIds: new Set(),
};

// ===========================
// Initialisation
// ===========================

/**
 * Initialise le système de notifications.
 * À appeler une fois que l'utilisateur est authentifié (rôle manager/admin/entreprise).
 */
function initNotifications() {
    // Ne pas afficher la cloche pour les rôles non concernés
    const user = AppState.currentUser;
    if (!user || user.role === 'employee') {
        const wrapper = document.getElementById('notificationBellWrapper');
        if (wrapper) wrapper.style.display = 'none';
        return;
    }

    setupNotificationListeners();
    fetchNotifications();

    // Polling toutes les 60 secondes
    NotifState.pollInterval = setInterval(fetchNotifications, 60000);
}

// ===========================
// API
// ===========================

/**
 * Récupère les alarmes dues depuis l'API et met à jour l'interface.
 *
 * @returns {Promise<void>}
 */
async function fetchNotifications() {
    try {
        const data = await apiGet(API_ENDPOINTS.NOTIFICATIONS);
        if (!data) return;

        const previous = NotifState.unreadCount;
        NotifState.notifications = data.notifications || [];
        NotifState.unreadCount = data.unread_count || 0;

        updateBadge(NotifState.unreadCount);
        renderNotificationList(NotifState.notifications);

        // Toast si de nouvelles alarmes sont apparues
        const newNotifs = NotifState.notifications.filter(
            n => !NotifState.seenIds.has(n.id)
        );
        if (newNotifs.length > 0 && previous !== null) {
            newNotifs.forEach(n => {
                NotifState.seenIds.add(n.id);
                showNotifToast(n);
            });
        } else {
            // Initialisation : enregistrer les IDs existants sans toast
            NotifState.notifications.forEach(n => NotifState.seenIds.add(n.id));
        }
    } catch (err) {
        console.error('Erreur chargement alarmes:', err);
    }
}

/**
 * Marque une alarme comme lue.
 *
 * @param {number} id - Identifiant de l'alarme.
 * @returns {Promise<void>}
 */
async function markNotifRead(id) {
    const result = await apiPost(API_ENDPOINTS.NOTIFICATION_MARK_READ(id), {});
    if (result && result.ok) {
        await fetchNotifications();
    }
}

/**
 * Marque toutes les alarmes comme lues.
 *
 * @returns {Promise<void>}
 */
async function markAllNotifsRead() {
    const result = await apiPost(API_ENDPOINTS.NOTIFICATIONS_MARK_ALL_READ, {});
    if (result && result.ok) {
        await fetchNotifications();
    }
}

// ===========================
// Rendu
// ===========================

/**
 * Met à jour le badge de la cloche.
 *
 * @param {number} count - Nombre d'alarmes non lues.
 */
function updateBadge(count) {
    const badge = document.getElementById('notificationBadge');
    if (!badge) return;
    if (count > 0) {
        badge.textContent = count > 99 ? '99+' : count;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}

/**
 * Construit la liste des alarmes dans le dropdown.
 *
 * @param {Object[]} notifications - Liste des alarmes retournées par l'API.
 */
function renderNotificationList(notifications) {
    const list = document.getElementById('notificationList');
    if (!list) return;

    if (notifications.length === 0) {
        list.innerHTML = '<li class="notification-empty">Aucune alarme en attente</li>';
        return;
    }

    list.innerHTML = notifications.map(n => {
        const icon = n.notification_type === '7days'
            ? 'fa-calendar-check'
            : 'fa-bell';
        const tagClass = n.notification_type === '7days'
            ? 'notif-tag-7days'
            : 'notif-tag-eve';
        const tagLabel = n.notification_type === '7days'
            ? 'J-7'
            : 'Veille';
        const days = n.days_until_start;
        const daysLabel = days > 0
            ? `dans ${days} jour${days > 1 ? 's' : ''}`
            : days === 0
                ? "commence aujourd'hui"
                : `commencé il y a ${Math.abs(days)} jour${Math.abs(days) > 1 ? 's' : ''}`;

        return `
        <li class="notification-item" data-id="${n.id}">
            <div class="notif-icon-col">
                <i class="fas ${icon}"></i>
            </div>
            <div class="notif-content-col">
                <div class="notif-header-row">
                    <span class="notif-employee">${escapeHtml(n.employee_name)}</span>
                    <span class="notif-tag ${tagClass}">${tagLabel}</span>
                </div>
                <div class="notif-detail">
                    ${escapeHtml(n.leave_type_display)} &bull;
                    Du ${formatDate(n.leave_start_date)} au ${formatDate(n.leave_end_date)}
                </div>
                <div class="notif-days">${daysLabel}</div>
            </div>
            <button class="notif-read-btn" onclick="markNotifRead(${n.id})" title="Marquer comme lu">
                <i class="fas fa-check"></i>
            </button>
        </li>`;
    }).join('');
}

/**
 * Joue un son de cloche d'alerte via l'API Web Audio (sans fichier externe).
 * Son différent selon le type : J-7 = double ding doux, Veille = triple ding urgent.
 *
 * @param {'7days'|'eve'} type - Type d'alarme.
 */
function playNotifSound(type) {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();

        // Paramètres selon le type d'alarme
        const isEve = type === 'eve';
        const freqs   = isEve ? [880, 1100, 880] : [880, 1046];
        const delays  = isEve ? [0, 0.18, 0.36]  : [0, 0.22];
        const volume  = isEve ? 0.35 : 0.25;

        freqs.forEach((freq, i) => {
            const osc    = ctx.createOscillator();
            const gain   = ctx.createGain();
            const start  = ctx.currentTime + delays[i];
            const end    = start + 0.35;

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, start);

            gain.gain.setValueAtTime(0, start);
            gain.gain.linearRampToValueAtTime(volume, start + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.001, end);

            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start(start);
            osc.stop(end);
        });

        // Libérer le contexte après lecture
        const totalDuration = (delays[delays.length - 1] + 0.5) * 1000;
        setTimeout(() => ctx.close(), totalDuration);

    } catch (e) {
        // Web Audio non supporté : silencieux
    }
}

/**
 * Affiche un toast en haut de l'écran pour une nouvelle alarme,
 * accompagné d'un son de cloche.
 *
 * @param {Object} notif - Objet notification.
 */
function showNotifToast(notif) {
    const label = notif.notification_type === '7days'
        ? '7 jours avant le congé'
        : 'Veille du congé';
    const msg = `Rappel : ${notif.employee_name} — ${notif.leave_type_display} (${label})`;

    // Son d'alerte
    playNotifSound(notif.notification_type);

    const toast = document.createElement('div');
    toast.className = 'notif-toast';
    toast.innerHTML = `
        <i class="fas fa-bell notif-toast-icon"></i>
        <span>${escapeHtml(msg)}</span>
        <button class="notif-toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>`;

    document.body.appendChild(toast);

    // Entrée animée
    requestAnimationFrame(() => toast.classList.add('notif-toast-visible'));

    // Suppression automatique après 7 secondes
    setTimeout(() => {
        toast.classList.remove('notif-toast-visible');
        setTimeout(() => toast.remove(), 400);
    }, 7000);
}

// ===========================
// Écouteurs d'événements
// ===========================

/**
 * Attache les écouteurs sur la cloche et le bouton "Tout marquer lu".
 */
function setupNotificationListeners() {
    const bellBtn = document.getElementById('notificationBellBtn');
    const dropdown = document.getElementById('notificationDropdown');
    const markAllBtn = document.getElementById('notifMarkAllBtn');

    if (bellBtn && dropdown) {
        bellBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            const isOpen = dropdown.style.display === 'block';
            dropdown.style.display = isOpen ? 'none' : 'block';
        });

        // Fermer en cliquant ailleurs
        document.addEventListener('click', function(e) {
            if (!bellBtn.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.style.display = 'none';
            }
        });
    }

    if (markAllBtn) {
        markAllBtn.addEventListener('click', async function() {
            await markAllNotifsRead();
            const dropdown = document.getElementById('notificationDropdown');
            if (dropdown) dropdown.style.display = 'none';
        });
    }
}

// Exposer pour usage global (onclick dans le HTML)
window.markNotifRead = markNotifRead;
window.initNotifications = initNotifications;
