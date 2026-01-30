// ===========================
// Connexion avec l'API Backend Django
// ===========================

// ===========================
// Initialisation
// ===========================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Login page loaded');

    // Attacher d'abord tous les event listeners
    // Gérer la soumission du formulaire de connexion
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
        console.log('Login form listener attached');
    }

    // Gérer la soumission du formulaire d'inscription
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
        console.log('Register form listener attached');
    }

    // Liens pour basculer entre connexion et inscription
    const showRegisterLink = document.getElementById('showRegisterLink');
    if (showRegisterLink) {
        showRegisterLink.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Show register clicked');
            showRegisterForm(e);
        });
        console.log('Show register link listener attached');
    } else {
        console.log('showRegisterLink not found!');
    }

    const showLoginLink = document.getElementById('showLoginLink');
    if (showLoginLink) {
        showLoginLink.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Show login clicked');
            showLoginForm(e);
        });
        console.log('Show login link listener attached');
    }

    // Vérifier si l'utilisateur est déjà connecté (à la fin)
    if (typeof isAuthenticated === 'function' && isAuthenticated()) {
        const currentUser = getCurrentUser();
        // Rediriger selon le rôle
        if (currentUser?.role === 'employee') {
            window.location.href = 'employee-profile.html';
        } else {
            window.location.href = 'dashboard.html';
        }
        return;
    }
});

// ===========================
// Basculer entre Connexion et Inscription
// ===========================
function showRegisterForm(e) {
    if (e && e.preventDefault) e.preventDefault();
    console.log('showRegisterForm called');

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const switchToRegister = document.getElementById('switchToRegister');
    const switchToLogin = document.getElementById('switchToLogin');

    if (loginForm) loginForm.classList.add('hidden');
    if (registerForm) registerForm.classList.remove('hidden');
    if (switchToRegister) switchToRegister.classList.add('hidden');
    if (switchToLogin) switchToLogin.classList.remove('hidden');

    // Mettre à jour le titre
    const h1 = document.querySelector('.login-header h1');
    const p = document.querySelector('.login-header p');
    if (h1) h1.textContent = 'Créer un compte';
    if (p) p.textContent = 'Rejoignez EmpManager';

    console.log('Register form should now be visible');
}

function showLoginForm(e) {
    if (e && e.preventDefault) e.preventDefault();
    console.log('showLoginForm called');

    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const switchToRegister = document.getElementById('switchToRegister');
    const switchToLogin = document.getElementById('switchToLogin');

    if (registerForm) registerForm.classList.add('hidden');
    if (loginForm) loginForm.classList.remove('hidden');
    if (switchToLogin) switchToLogin.classList.add('hidden');
    if (switchToRegister) switchToRegister.classList.remove('hidden');

    // Mettre à jour le titre
    const h1 = document.querySelector('.login-header h1');
    const p = document.querySelector('.login-header p');
    if (h1) h1.textContent = 'EmpManager';
    if (p) p.textContent = 'Système de Gestion du Personnel';

    console.log('Login form should now be visible');
}

// ===========================
// Authentification via API
// ===========================
async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('userRole').value;

    // Validation
    if (!username || !password || !role) {
        showError('Veuillez remplir tous les champs.');
        return;
    }

    // Afficher le chargement
    const submitBtn = document.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connexion en cours...';
    submitBtn.disabled = true;

    try {
        const response = await fetch(API_ENDPOINTS.LOGIN, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password, role })
        });

        const data = await response.json();

        if (response.ok) {
            // Stocker les tokens et les infos utilisateur
            storeAuthData(data);

            // Stocker le rôle dans currentUser
            const currentUser = getCurrentUser();
            if (currentUser) {
                currentUser.role = role;
                sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
            }

            // Rediriger selon le rôle
            if (role === 'employee') {
                window.location.href = 'employee-profile.html';
            } else {
                window.location.href = 'dashboard.html';
            }
        } else {
            // Afficher l'erreur
            showError(data.error || 'Identifiants incorrects. Veuillez réessayer.');
        }
    } catch (error) {
        console.error('Erreur de connexion:', error);
        showError('Erreur de connexion au serveur. Vérifiez que le backend est démarré.');
    } finally {
        // Restaurer le bouton
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// ===========================
// Inscription via API
// ===========================
async function handleRegister(e) {
    e.preventDefault();

    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;
    const role = document.getElementById('regRole').value;

    // Validation
    if (!username || !email || !password || !confirmPassword || !role) {
        showError('Veuillez remplir tous les champs.');
        return;
    }

    if (password !== confirmPassword) {
        showError('Les mots de passe ne correspondent pas.');
        return;
    }

    if (password.length < 6) {
        showError('Le mot de passe doit contenir au moins 6 caractères.');
        return;
    }

    // Afficher le chargement
    const submitBtn = document.querySelector('#registerForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Création en cours...';
    submitBtn.disabled = true;

    try {
        const response = await fetch(API_ENDPOINTS.REGISTER, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username,
                email,
                password,
                password2: confirmPassword,
                role
            })
        });

        const data = await response.json();

        if (response.ok) {
            // Stocker les tokens et les infos utilisateur
            storeAuthData(data);

            // Ajouter le rôle et l'email aux infos utilisateur
            const currentUser = getCurrentUser();
            if (currentUser) {
                currentUser.role = role;
                currentUser.email = email;
                sessionStorage.setItem('currentUser', JSON.stringify(currentUser));
            }

            // Si c'est un employé, rediriger vers la page de profil
            if (role === 'employee') {
                showSuccess('Compte créé ! Complétez votre profil...');
                setTimeout(() => {
                    window.location.href = 'employee-profile.html';
                }, 1500);
            } else {
                // Pour admin et manager, rediriger vers le dashboard
                showSuccess('Compte créé avec succès !');
                setTimeout(() => {
                    window.location.href = 'dashboard.html';
                }, 1500);
            }
        } else {
            // Afficher l'erreur
            showError(data.error || data.username?.[0] || data.email?.[0] || 'Erreur lors de la création du compte.');
        }
    } catch (error) {
        console.error('Erreur d\'inscription:', error);
        showError('Erreur de connexion au serveur. Vérifiez que le backend est démarré.');
    } finally {
        // Restaurer le bouton
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

// ===========================
// Affichage des messages
// ===========================
function showSuccess(message) {
    // Vérifier si un élément de succès existe déjà
    let successDiv = document.querySelector('.login-success');

    if (!successDiv) {
        successDiv = document.createElement('div');
        successDiv.className = 'login-success';
        successDiv.style.cssText = `
            background: #d1fae5;
            border: 1px solid #10b981;
            color: #059669;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
            font-weight: 600;
        `;

        const form = document.getElementById('registerForm');
        form.parentNode.insertBefore(successDiv, form);
    }

    successDiv.textContent = message;
    successDiv.style.display = 'block';

    // Masquer après 5 secondes
    setTimeout(() => {
        successDiv.style.display = 'none';
    }, 5000);
}

// ===========================
// Affichage des erreurs
// ===========================
function showError(message) {
    // Vérifier si un élément d'erreur existe déjà
    let errorDiv = document.querySelector('.login-error');

    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.className = 'login-error';
        errorDiv.style.cssText = `
            background: #fee2e2;
            border: 1px solid #ef4444;
            color: #dc2626;
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            text-align: center;
            font-weight: 600;
        `;

        // Insérer avant le formulaire actif
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const activeForm = loginForm.classList.contains('hidden') ? registerForm : loginForm;
        activeForm.parentNode.insertBefore(errorDiv, activeForm);
    }

    errorDiv.textContent = message;
    errorDiv.style.display = 'block';

    // Masquer l'erreur après 5 secondes
    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}
