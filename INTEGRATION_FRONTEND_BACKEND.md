# Intégration Frontend-Backend EmpManager

## Vue d'ensemble

Ce document explique comment intégrer le frontend HTML/CSS/JS existant avec le backend Django REST API.

## Architecture

```
Frontend (HTML/CSS/JS)  <--HTTP/JSON-->  Backend (Django REST API)  <-->  PostgreSQL
```

## Configuration requise

### Backend
1. **Installer PostgreSQL** : Téléchargez et installez PostgreSQL depuis https://www.postgresql.org/download/
2. **Créer la base de données** :
   ```sql
   CREATE DATABASE empmanager_db;
   ```

3. **Configurer le backend** :
   ```bash
   cd backend
   # Windows
   setup.bat

   # Linux/Mac
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Démarrer le serveur Django** :
   ```bash
   python manage.py runserver
   ```
   Le serveur sera disponible sur `http://localhost:8000`

### Frontend
Le frontend existant doit être servi via un serveur HTTP. Vous pouvez utiliser :

#### Option 1: Live Server (VS Code)
1. Installer l'extension "Live Server" dans VS Code
2. Cliquer droit sur `index.html` → "Open with Live Server"

#### Option 2: Python HTTP Server
```bash
# Dans le dossier racine du projet
python -m http.server 8080
```
Accédez à `http://localhost:8080`

#### Option 3: Node.js http-server
```bash
npx http-server -p 8080
```

## Modifications du Frontend

### 1. Créer un fichier de configuration API

Créez `api-config.js` :

```javascript
const API_BASE_URL = 'http://localhost:8000/api';

const API_ENDPOINTS = {
    // Auth
    LOGIN: `${API_BASE_URL}/auth/login/`,
    REGISTER: `${API_BASE_URL}/auth/register/`,
    TOKEN: `${API_BASE_URL}/token/`,
    TOKEN_REFRESH: `${API_BASE_URL}/token/refresh/`,

    // Dashboard
    DASHBOARD_STATS: `${API_BASE_URL}/dashboard/stats/`,

    // Departments
    DEPARTMENTS: `${API_BASE_URL}/departments/`,
    DEPARTMENT_DETAIL: (id) => `${API_BASE_URL}/departments/${id}/`,
    DEPARTMENT_EMPLOYEES: (id) => `${API_BASE_URL}/departments/${id}/employees/`,

    // Employees
    EMPLOYEES: `${API_BASE_URL}/employees/`,
    EMPLOYEE_DETAIL: (id) => `${API_BASE_URL}/employees/${id}/`,
    EMPLOYEES_BY_DEPARTMENT: `${API_BASE_URL}/employees/by_department/`,

    // Leaves
    LEAVES: `${API_BASE_URL}/leaves/`,
    LEAVE_DETAIL: (id) => `${API_BASE_URL}/leaves/${id}/`,
    LEAVE_APPROVE: (id) => `${API_BASE_URL}/leaves/${id}/approve/`,
    LEAVE_REJECT: (id) => `${API_BASE_URL}/leaves/${id}/reject/`,
    LEAVES_PENDING: `${API_BASE_URL}/leaves/pending/`,

    // Attendances
    ATTENDANCES: `${API_BASE_URL}/attendances/`,
    ATTENDANCE_DETAIL: (id) => `${API_BASE_URL}/attendances/${id}/`,
    ATTENDANCES_TODAY: `${API_BASE_URL}/attendances/today/`,
    ATTENDANCES_BY_EMPLOYEE: `${API_BASE_URL}/attendances/by_employee/`,
};

// Helper pour les requêtes API avec authentification
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('access_token');

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
            ...(token && { 'Authorization': `Bearer ${token}` }),
        },
    };

    const response = await fetch(url, { ...defaultOptions, ...options });

    if (response.status === 401) {
        // Token expiré, essayer de rafraîchir
        const refreshed = await refreshToken();
        if (refreshed) {
            // Réessayer la requête
            const newToken = localStorage.getItem('access_token');
            options.headers = {
                ...options.headers,
                'Authorization': `Bearer ${newToken}`
            };
            return fetch(url, { ...defaultOptions, ...options });
        } else {
            // Rediriger vers login
            window.location.href = 'login.html';
            return null;
        }
    }

    return response;
}

async function refreshToken() {
    const refresh = localStorage.getItem('refresh_token');
    if (!refresh) return false;

    try {
        const response = await fetch(API_ENDPOINTS.TOKEN_REFRESH, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh })
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
```

### 2. Modifier `login.js`

Remplacez l'authentification locale par l'API :

```javascript
document.getElementById('loginForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('userRole').value;

    try {
        const response = await fetch(API_ENDPOINTS.LOGIN, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, role })
        });

        if (response.ok) {
            const data = await response.json();

            // Stocker les tokens
            localStorage.setItem('access_token', data.access);
            localStorage.setItem('refresh_token', data.refresh);

            // Stocker les infos utilisateur
            sessionStorage.setItem('currentUser', JSON.stringify(data.user));

            // Rediriger vers dashboard
            window.location.href = 'dashboard.html';
        } else {
            const error = await response.json();
            alert(error.error || 'Erreur de connexion');
        }
    } catch (error) {
        console.error('Erreur:', error);
        alert('Erreur de connexion au serveur');
    }
});
```

### 3. Modifier `dashboard.js`

Remplacez localStorage par les appels API :

```javascript
// Exemple pour charger les départements
async function loadDepartments() {
    try {
        const response = await apiRequest(API_ENDPOINTS.DEPARTMENTS);
        if (response && response.ok) {
            const departments = await response.json();
            AppState.departments = departments;
            renderDepartments();
        }
    } catch (error) {
        console.error('Erreur chargement départements:', error);
    }
}

// Exemple pour créer un employé
async function createEmployee(employeeData) {
    try {
        const response = await apiRequest(API_ENDPOINTS.EMPLOYEES, {
            method: 'POST',
            body: JSON.stringify(employeeData)
        });

        if (response && response.ok) {
            const newEmployee = await response.json();
            alert('Employé créé avec succès!');
            await loadEmployees();
        } else {
            const error = await response.json();
            alert('Erreur: ' + JSON.stringify(error));
        }
    } catch (error) {
        console.error('Erreur création employé:', error);
        alert('Erreur de connexion au serveur');
    }
}
```

## Utilisateurs de démonstration

Le backend est configuré avec 3 utilisateurs de test :

| Username | Password | Rôle |
|----------|----------|------|
| admin | admin123 | Administrateur |
| manager | manager123 | Manager |
| employee | employee123 | Employé |

## Flux d'authentification

1. L'utilisateur se connecte via `login.html`
2. Le frontend envoie username, password et role à `/api/auth/login/`
3. Le backend retourne un access_token et refresh_token
4. Le frontend stocke les tokens dans localStorage
5. Pour chaque requête API, le frontend inclut: `Authorization: Bearer {access_token}`
6. Si le token expire (401), le frontend utilise refresh_token pour obtenir un nouveau token
7. Si le refresh échoue, l'utilisateur est redirigé vers login

## Exemples d'intégration

### Charger les statistiques du dashboard

```javascript
async function loadDashboardStats() {
    const response = await apiRequest(API_ENDPOINTS.DASHBOARD_STATS);
    if (response && response.ok) {
        const stats = await response.json();
        document.getElementById('totalEmployees').textContent = stats.total_employees;
        document.getElementById('totalDepartments').textContent = stats.total_departments;
        document.getElementById('presentToday').textContent = stats.present_today;
        document.getElementById('onLeaveToday').textContent = stats.on_leave_today;
    }
}
```

### Créer un département

```javascript
async function createDepartment(name, manager, description) {
    const response = await apiRequest(API_ENDPOINTS.DEPARTMENTS, {
        method: 'POST',
        body: JSON.stringify({ name, manager, description })
    });

    if (response && response.ok) {
        const department = await response.json();
        return department;
    }
    return null;
}
```

### Approuver un congé

```javascript
async function approveLeave(leaveId) {
    const response = await apiRequest(API_ENDPOINTS.LEAVE_APPROVE(leaveId), {
        method: 'POST'
    });

    if (response && response.ok) {
        alert('Congé approuvé!');
        await loadLeaves();
    }
}
```

## Checklist d'intégration

- [ ] PostgreSQL installé et configuré
- [ ] Backend Django démarré (`python manage.py runserver`)
- [ ] Frontend servi via serveur HTTP
- [ ] Fichier `api-config.js` créé
- [ ] `login.js` modifié pour utiliser l'API
- [ ] `dashboard.js` modifié pour utiliser l'API
- [ ] CORS configuré dans Django settings
- [ ] Tokens JWT stockés dans localStorage
- [ ] Gestion du rafraîchissement des tokens
- [ ] Gestion des erreurs API
- [ ] Tests de connexion avec les 3 rôles

## Dépannage

### CORS Error
Si vous voyez des erreurs CORS, vérifiez que le frontend tourne sur un port autorisé dans `settings.py` :
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",  # Ajoutez votre port
]
```

### 401 Unauthorized
- Vérifiez que le token est bien stocké dans localStorage
- Vérifiez que le header Authorization est bien envoyé
- Essayez de vous reconnecter

### Connection Refused
- Vérifiez que le serveur Django est bien démarré
- Vérifiez l'URL de l'API dans `api-config.js`

## Prochaines étapes

1. **Migration complète** : Remplacer tous les appels localStorage par des appels API
2. **Gestion d'erreurs** : Ajouter des messages d'erreur utilisateur-friendly
3. **Loading states** : Ajouter des indicateurs de chargement
4. **Optimisations** : Cache local, pagination, recherche côté serveur
5. **Tests** : Tests end-to-end avec Cypress ou Selenium
