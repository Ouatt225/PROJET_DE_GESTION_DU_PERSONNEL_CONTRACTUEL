// ===========================
// Configuration de l'API Backend
// ===========================

const API_BASE_URL = 'http://localhost:8000/api';

const API_ENDPOINTS = {
    // Authentification
    LOGIN: `${API_BASE_URL}/auth/login/`,
    REGISTER: `${API_BASE_URL}/auth/register/`,
    TOKEN: `${API_BASE_URL}/token/`,
    TOKEN_REFRESH: `${API_BASE_URL}/token/refresh/`,

    // Dashboard
    DASHBOARD_STATS: `${API_BASE_URL}/dashboard/stats/`,

    // Directions
    DIRECTIONS: `${API_BASE_URL}/directions/`,

    // Entreprises
    DEPARTMENTS: `${API_BASE_URL}/departments/`,
    DEPARTMENT_DETAIL: (id) => `${API_BASE_URL}/departments/${id}/`,
    DEPARTMENT_EMPLOYEES: (id) => `${API_BASE_URL}/departments/${id}/employees/`,

    // Employés
    EMPLOYEES: `${API_BASE_URL}/employees/`,
    EMPLOYEE_DETAIL: (id) => `${API_BASE_URL}/employees/${id}/`,
    EMPLOYEES_BY_DEPARTMENT: `${API_BASE_URL}/employees/by_department/`,

    // Congés
    LEAVES: `${API_BASE_URL}/leaves/`,
    LEAVE_DETAIL: (id) => `${API_BASE_URL}/leaves/${id}/`,
    LEAVE_APPROVE: (id) => `${API_BASE_URL}/leaves/${id}/approve/`,
    LEAVE_REJECT: (id) => `${API_BASE_URL}/leaves/${id}/reject/`,
    LEAVES_PENDING: `${API_BASE_URL}/leaves/pending/`,

    // Présences
    ATTENDANCES: `${API_BASE_URL}/attendances/`,
    ATTENDANCE_DETAIL: (id) => `${API_BASE_URL}/attendances/${id}/`,
    ATTENDANCES_TODAY: `${API_BASE_URL}/attendances/today/`,
    ATTENDANCES_BY_EMPLOYEE: `${API_BASE_URL}/attendances/by_employee/`,

    // Rapports
    REPORT_ATTENDANCE: `${API_BASE_URL}/reports/attendance/`,
    REPORT_LEAVES: `${API_BASE_URL}/reports/leaves/`,
    REPORT_DEPARTMENTS: `${API_BASE_URL}/reports/departments/`,
    REPORT_COMPLETE: `${API_BASE_URL}/reports/complete/`,

};

// ===========================
// Fonctions utilitaires pour l'API
// ===========================

/**
 * Effectue une requête API avec authentification JWT
 * @param {string} url - L'URL de l'endpoint
 * @param {object} options - Options de fetch (method, body, etc.)
 * @returns {Promise<Response>} - La réponse de l'API
 */
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('access_token');

    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    };

    try {
        let response = await fetch(url, config);

        // Si token expiré (401), essayer de rafraîchir
        if (response.status === 401 && token) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                // Réessayer avec le nouveau token
                const newToken = localStorage.getItem('access_token');
                config.headers['Authorization'] = `Bearer ${newToken}`;
                response = await fetch(url, config);
            } else {
                // Échec du rafraîchissement, rediriger vers login
                handleLogoutRedirect();
                return null;
            }
        }

        return response;
    } catch (error) {
        console.error('Erreur API:', error);
        throw error;
    }
}

/**
 * Rafraîchit le token d'accès
 * @returns {Promise<boolean>} - true si réussi, false sinon
 */
async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');

    if (!refreshToken) {
        return false;
    }

    try {
        const response = await fetch(API_ENDPOINTS.TOKEN_REFRESH, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access);
            return true;
        }
    } catch (error) {
        console.error('Erreur rafraîchissement token:', error);
    }

    return false;
}

/**
 * Redirige vers la page de connexion
 */
function handleLogoutRedirect() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('currentUser');
    window.location.href = 'login.html';
}

/**
 * Vérifie si l'utilisateur est authentifié
 * @returns {boolean}
 */
function isAuthenticated() {
    return localStorage.getItem('access_token') !== null;
}

/**
 * Stocke les informations d'authentification
 * @param {object} data - Données de connexion (user, access, refresh)
 */
function storeAuthData(data) {
    localStorage.setItem('access_token', data.access);
    localStorage.setItem('refresh_token', data.refresh);
    sessionStorage.setItem('currentUser', JSON.stringify(data.user));
}

/**
 * Récupère l'utilisateur courant
 * @returns {object|null}
 */
function getCurrentUser() {
    const user = sessionStorage.getItem('currentUser');
    return user ? JSON.parse(user) : null;
}

// ===========================
// Fonctions CRUD génériques
// ===========================

/**
 * GET - Récupérer une liste
 */
async function apiGet(url) {
    const response = await apiRequest(url);
    if (response && response.ok) {
        return await response.json();
    }
    return null;
}

/**
 * POST - Créer une ressource
 */
async function apiPost(url, data) {
    const response = await apiRequest(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });

    if (response) {
        const result = await response.json();
        return { ok: response.ok, data: result, status: response.status };
    }
    return { ok: false, data: null, status: 0 };
}

/**
 * PUT - Mettre à jour une ressource
 */
async function apiPut(url, data) {
    const response = await apiRequest(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    });

    if (response) {
        const result = await response.json();
        return { ok: response.ok, data: result, status: response.status };
    }
    return { ok: false, data: null, status: 0 };
}

/**
 * DELETE - Supprimer une ressource
 */
async function apiDelete(url) {
    const response = await apiRequest(url, {
        method: 'DELETE'
    });

    if (response) {
        return { ok: response.ok, status: response.status };
    }
    return { ok: false, status: 0 };
}

/**
 * POST avec FormData - Pour envoyer des fichiers
 */
async function apiPostFormData(url, formData) {
    const token = localStorage.getItem('access_token');

    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }
    // Ne pas définir Content-Type, le navigateur le fera automatiquement avec le boundary

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: headers,
            body: formData
        });

        const result = await response.json();
        return { ok: response.ok, data: result, status: response.status };
    } catch (error) {
        console.error('Erreur API FormData:', error);
        return { ok: false, data: null, status: 0 };
    }
}

/**
 * PUT avec FormData - Pour mettre à jour avec des fichiers
 */
async function apiPutFormData(url, formData) {
    const token = localStorage.getItem('access_token');

    const headers = {};
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        // Utiliser PATCH au lieu de PUT pour les mises à jour partielles avec fichiers
        const response = await fetch(url, {
            method: 'PATCH',
            headers: headers,
            body: formData
        });

        const result = await response.json();
        return { ok: response.ok, data: result, status: response.status };
    } catch (error) {
        console.error('Erreur API FormData:', error);
        return { ok: false, data: null, status: 0 };
    }
}

// Exporter pour utilisation globale
window.API_ENDPOINTS = API_ENDPOINTS;
window.apiRequest = apiRequest;
window.apiGet = apiGet;
window.apiPost = apiPost;
window.apiPut = apiPut;
window.apiDelete = apiDelete;
window.apiPostFormData = apiPostFormData;
window.apiPutFormData = apiPutFormData;
window.isAuthenticated = isAuthenticated;
window.storeAuthData = storeAuthData;
window.getCurrentUser = getCurrentUser;
window.handleLogoutRedirect = handleLogoutRedirect;
