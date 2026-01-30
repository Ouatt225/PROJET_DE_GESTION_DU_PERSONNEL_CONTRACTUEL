// ===========================
// Espace Contractuel - Gestion du profil employé
// ===========================

let currentEmployee = null;
let departments = [];

document.addEventListener('DOMContentLoaded', function() {
    console.log('Espace Contractuel loaded');

    // Vérifier l'authentification
    if (!isAuthenticated()) {
        window.location.href = 'login.html';
        return;
    }

    // Initialiser l'application
    initializeApp();
});

async function initializeApp() {
    // Charger les entreprises/départements
    await loadCompanies();

    // Charger le profil de l'employé
    await loadEmployeeProfile();

    // Charger les congés
    await loadEmployeeLeaves();

    // Configurer les événements
    setupEventListeners();
}

// ===========================
// Chargement des données
// ===========================

async function loadCompanies() {
    try {
        const response = await apiGet(API_ENDPOINTS.DEPARTMENTS);
        if (response) {
            departments = response.results || response;
            const companySelect = document.getElementById('company');
            if (companySelect) {
                departments.forEach(dept => {
                    const option = document.createElement('option');
                    option.value = dept.id;
                    option.textContent = dept.name;
                    companySelect.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Erreur chargement entreprises:', error);
    }
}

async function loadEmployeeProfile() {
    const currentUser = getCurrentUser();

    console.log('Utilisateur connecté:', currentUser);

    // Afficher le nom dans la sidebar
    document.getElementById('employeeName').textContent = currentUser?.name || currentUser?.username || 'Employé';

    try {
        // Chercher l'employé par email ou user_id
        const employees = await apiGet(API_ENDPOINTS.EMPLOYEES);
        console.log('Liste des employés:', employees);

        if (employees) {
            const employeeList = employees.results || employees;

            // Trouver l'employé correspondant à l'utilisateur connecté
            // Priorité 1: par user ID
            // Priorité 2: par email de l'utilisateur
            // Priorité 3: par username (si l'email de l'employé contient le username)
            currentEmployee = employeeList.find(emp => emp.user === currentUser?.id);

            if (!currentEmployee && currentUser?.email) {
                currentEmployee = employeeList.find(emp => emp.email === currentUser.email);
            }

            if (!currentEmployee && currentUser?.username) {
                currentEmployee = employeeList.find(emp =>
                    emp.email?.toLowerCase().includes(currentUser.username.toLowerCase())
                );
            }

            console.log('Employé trouvé:', currentEmployee);

            if (currentEmployee) {
                displayProfile(currentEmployee);
                fillEditForm(currentEmployee);
            } else {
                // Pas de profil trouvé, pré-remplir l'email si disponible
                if (currentUser?.email) {
                    const emailField = document.getElementById('email');
                    if (emailField) emailField.value = currentUser.email;
                }
                showNotification('Veuillez compléter votre profil', 'info');
                switchSection('edit-profile');
            }
        }
    } catch (error) {
        console.error('Erreur chargement profil:', error);
    }
}

async function loadEmployeeLeaves() {
    if (!currentEmployee) return;

    try {
        const leaves = await apiGet(API_ENDPOINTS.LEAVES);
        if (leaves) {
            const leaveList = leaves.results || leaves;
            // Filtrer les congés de l'employé
            const myLeaves = leaveList.filter(leave => leave.employee === currentEmployee.id);
            displayLeaves(myLeaves);
            updateLeaveStats(myLeaves);
        }
    } catch (error) {
        console.error('Erreur chargement congés:', error);
    }
}

// ===========================
// Affichage des données
// ===========================

function displayProfile(employee) {
    // Informations personnelles
    document.getElementById('viewFullName').textContent = employee.full_name || `${employee.first_name} ${employee.last_name}`;
    document.getElementById('viewBirthDate').textContent = formatDate(employee.birth_date) || '-';
    document.getElementById('viewMaritalStatus').textContent = getMaritalStatusLabel(employee.marital_status) || '-';
    document.getElementById('viewChildren').textContent = employee.number_of_children ?? '-';

    // Âge et retraite
    if (employee.birth_date) {
        const age = calculateAge(employee.birth_date);
        const retirementYear = calculateRetirementYear(employee.birth_date);
        document.getElementById('viewAge').textContent = age ? `${age} ans` : '-';
        document.getElementById('viewRetirementYear').textContent = retirementYear || '-';
    } else {
        document.getElementById('viewAge').textContent = '-';
        document.getElementById('viewRetirementYear').textContent = '-';
    }

    // Sexe
    document.getElementById('viewGender').textContent = getGenderLabel(employee.gender) || '-';

    // Coordonnées
    document.getElementById('viewEmail').textContent = employee.email || '-';
    document.getElementById('viewPhone').textContent = employee.phone || '-';
    document.getElementById('viewCity').textContent = employee.city || '-';
    document.getElementById('viewCommune').textContent = employee.commune || '-';

    // Informations professionnelles
    document.getElementById('viewCompany').textContent = employee.department_name || getDepartmentName(employee.department) || '-';
    document.getElementById('viewPosition').textContent = employee.position || '-';
    document.getElementById('viewHireDate').textContent = formatDate(employee.hire_date) || '-';
    document.getElementById('viewSalary').textContent = employee.salary ? formatCurrency(employee.salary) : '-';
    document.getElementById('viewCNPS').textContent = employee.cnps || '-';

    // Mettre à jour le nom dans la sidebar
    document.getElementById('employeeName').textContent = employee.full_name || `${employee.first_name} ${employee.last_name}`;
}

function fillEditForm(employee) {
    document.getElementById('employeeId').value = employee.id || '';
    document.getElementById('firstName').value = employee.first_name || '';
    document.getElementById('lastName').value = employee.last_name || '';
    document.getElementById('birthDate').value = employee.birth_date || '';
    document.getElementById('maritalStatus').value = employee.marital_status || '';

    // Afficher l'info de retraite si date de naissance présente
    if (employee.birth_date) {
        handleBirthDateChange(employee.birth_date);
    }
    document.getElementById('gender').value = employee.gender || '';
    document.getElementById('numberOfChildren').value = employee.number_of_children || 0;
    document.getElementById('email').value = employee.email || '';
    document.getElementById('phone').value = employee.phone || '';
    document.getElementById('city').value = employee.city || '';
    document.getElementById('commune').value = employee.commune || '';
    document.getElementById('company').value = employee.department || '';
    document.getElementById('position').value = employee.position || '';
    document.getElementById('hireDate').value = employee.hire_date || '';
    document.getElementById('salary').value = employee.salary || '';
    document.getElementById('cnpsNumber').value = employee.cnps || '';

    // Afficher la photo existante
    const photoPreview = document.getElementById('photoPreview');
    if (employee.photo && photoPreview) {
        photoPreview.innerHTML = `<img src="${employee.photo}" alt="Photo">`;
    }

    // Afficher la CNI existante
    const cniPreview = document.getElementById('cniPreview');
    if (employee.cni_document && cniPreview) {
        cniPreview.classList.add('has-file');
        const fileName = employee.cni_document.split('/').pop();
        const isPdf = employee.cni_document.endsWith('.pdf');
        cniPreview.innerHTML = `
            <i class="fas ${isPdf ? 'fa-file-pdf' : 'fa-image'}"></i>
            <span>${fileName}</span>
            <a href="${employee.cni_document}" target="_blank" class="btn btn-sm btn-secondary" style="margin-top: 0.5rem;">
                <i class="fas fa-eye"></i> Voir
            </a>
        `;
    }
}

function displayLeaves(leaves) {
    const tbody = document.getElementById('leavesTableBody');

    if (!leaves || leaves.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="text-align: center; padding: 2rem; color: var(--text-secondary);">
                    <i class="fas fa-calendar-times" style="font-size: 2rem; margin-bottom: 0.5rem; display: block;"></i>
                    Aucune demande de congé
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = leaves.map(leave => `
        <tr>
            <td>${getLeaveTypeLabel(leave.leave_type)}</td>
            <td>${formatDate(leave.start_date)}</td>
            <td>${formatDate(leave.end_date)}</td>
            <td>${leave.days_count || calculateDays(leave.start_date, leave.end_date)}</td>
            <td>${leave.reason || '-'}</td>
            <td><span class="status-badge status-${leave.status}">${getStatusLabel(leave.status)}</span></td>
        </tr>
    `).join('');
}

function updateLeaveStats(leaves) {
    // Statistiques des demandes
    document.getElementById('totalLeaves').textContent = leaves.length;
    document.getElementById('pendingLeaves').textContent = leaves.filter(l => l.status === 'pending').length;

    // Mise à jour du solde de congés depuis les données de l'employé
    if (currentEmployee) {
        const balance = currentEmployee.leave_balance ?? 30;
        const taken = currentEmployee.leaves_taken_this_year ?? 0;

        // Section "Mes Congés"
        const leaveBalanceEl = document.getElementById('leaveBalance');
        const leavesTakenEl = document.getElementById('leavesTaken');
        if (leaveBalanceEl) leaveBalanceEl.textContent = balance;
        if (leavesTakenEl) leavesTakenEl.textContent = taken;

        // Section "Demander un congé"
        const leaveBalanceFormEl = document.getElementById('leaveBalanceForm');
        const leavesTakenFormEl = document.getElementById('leavesTakenForm');
        if (leaveBalanceFormEl) leaveBalanceFormEl.textContent = balance;
        if (leavesTakenFormEl) leavesTakenFormEl.textContent = taken;
    }
}

// ===========================
// Navigation
// ===========================

function switchSection(sectionName) {
    // Mapping des noms de sections
    const sectionMap = {
        'profile': 'profileSection',
        'edit-profile': 'editProfileSection',
        'leaves': 'leavesSection',
        'request-leave': 'requestLeaveSection'
    };

    const sectionId = sectionMap[sectionName];
    if (!sectionId) return;

    // Masquer toutes les sections
    document.querySelectorAll('.employee-section').forEach(section => {
        section.classList.remove('active');
    });

    // Afficher la section sélectionnée
    document.getElementById(sectionId).classList.add('active');

    // Mettre à jour la navigation
    document.querySelectorAll('.employee-nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.section === sectionName) {
            item.classList.add('active');
        }
    });

    // Fermer le menu mobile
    document.getElementById('employeeSidebar')?.classList.remove('open');
}

// Exposer la fonction globalement
window.switchSection = switchSection;

// ===========================
// Événements
// ===========================

function setupEventListeners() {
    // Navigation
    document.querySelectorAll('.employee-nav-item').forEach(item => {
        item.addEventListener('click', function() {
            switchSection(this.dataset.section);
        });
    });

    // Formulaire de profil
    document.getElementById('employeeProfileForm')?.addEventListener('submit', handleProfileSubmit);

    // Formulaire de demande de congé
    document.getElementById('leaveRequestForm')?.addEventListener('submit', handleLeaveSubmit);

    // Déconnexion
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);

    // Téléchargement du profil en PDF
    document.getElementById('downloadProfileBtn')?.addEventListener('click', generateProfilePDF);

    // Menu mobile
    document.getElementById('mobileToggle')?.addEventListener('click', function() {
        document.getElementById('employeeSidebar')?.classList.toggle('open');
    });

    // Gestion des fichiers - Photo d'identité
    document.getElementById('photo')?.addEventListener('change', function(e) {
        handleFilePreview(e.target, 'photoPreview', true);
    });

    // Gestion des fichiers - CNI
    document.getElementById('cniDocument')?.addEventListener('change', function(e) {
        handleFilePreview(e.target, 'cniPreview', false);
    });

    // Validation de la date de naissance et calcul de la retraite
    document.getElementById('birthDate')?.addEventListener('change', function(e) {
        handleBirthDateChange(e.target.value);
    });
}

/**
 * Gère le changement de la date de naissance
 * Valide l'âge et affiche l'année de retraite
 */
function handleBirthDateChange(birthDate) {
    const retirementInfoEl = document.getElementById('retirementInfo');
    const birthDateInput = document.getElementById('birthDate');

    if (!birthDate) {
        if (retirementInfoEl) retirementInfoEl.style.display = 'none';
        birthDateInput.classList.remove('input-error');
        return;
    }

    const ageValidation = validateEmployeeAge(birthDate);

    if (!ageValidation.valid) {
        birthDateInput.classList.add('input-error');
        showNotification(ageValidation.message, 'error');
        if (retirementInfoEl) retirementInfoEl.style.display = 'none';
    } else {
        birthDateInput.classList.remove('input-error');
        const retirementYear = calculateRetirementYear(birthDate);
        if (retirementInfoEl && retirementYear) {
            document.getElementById('retirementYear').textContent = retirementYear;
            document.getElementById('currentAge').textContent = ageValidation.age;
            retirementInfoEl.style.display = 'flex';
        }
    }
}

// Fonction pour gérer l'aperçu des fichiers
function handleFilePreview(input, previewId, isPhoto) {
    const preview = document.getElementById(previewId);
    const file = input.files[0];

    if (file) {
        // Vérifier la taille du fichier
        const maxSize = isPhoto ? 2 * 1024 * 1024 : 5 * 1024 * 1024; // 2MB pour photo, 5MB pour CNI
        if (file.size > maxSize) {
            showNotification(`Le fichier est trop volumineux (max ${isPhoto ? '2' : '5'} Mo)`, 'error');
            input.value = '';
            return;
        }

        if (isPhoto) {
            // Aperçu de la photo
            const reader = new FileReader();
            reader.onload = function(e) {
                preview.innerHTML = `<img src="${e.target.result}" alt="Photo">`;
            };
            reader.readAsDataURL(file);
        } else {
            // Aperçu du document CNI
            preview.classList.add('has-file');
            const icon = file.type === 'application/pdf' ? 'fa-file-pdf' : 'fa-image';
            preview.innerHTML = `
                <i class="fas ${icon}"></i>
                <span>${file.name}</span>
            `;
        }
    }
}

// ===========================
// Soumission des formulaires
// ===========================

async function handleProfileSubmit(e) {
    e.preventDefault();

    const currentUser = getCurrentUser();
    const employeeId = document.getElementById('employeeId').value;
    const isNewEmployee = !employeeId;

    // Valider l'âge de l'employé
    const birthDate = document.getElementById('birthDate').value;
    if (birthDate) {
        const ageValidation = validateEmployeeAge(birthDate);
        if (!ageValidation.valid) {
            showNotification(ageValidation.message, 'error');
            document.getElementById('birthDate').focus();
            return;
        }
    }

    // Valider les fichiers obligatoires pour les nouveaux employés
    const photoInput = document.getElementById('photo');
    const cniInput = document.getElementById('cniDocument');

    if (isNewEmployee) {
        if (!photoInput.files[0]) {
            showNotification('La photo d\'identité est obligatoire', 'error');
            return;
        }
        if (!cniInput.files[0]) {
            showNotification('La Carte Nationale d\'Identité est obligatoire', 'error');
            return;
        }
    }

    // Utiliser FormData pour pouvoir envoyer des fichiers
    const formData = new FormData();

    // Ajouter les champs texte (tous obligatoires sauf commune)
    formData.append('first_name', document.getElementById('firstName').value);
    formData.append('last_name', document.getElementById('lastName').value);
    formData.append('email', document.getElementById('email').value);
    formData.append('position', document.getElementById('position').value);
    formData.append('hire_date', document.getElementById('hireDate').value);
    formData.append('department', document.getElementById('company').value);
    formData.append('status', 'active');

    // Champs obligatoires
    formData.append('birth_date', document.getElementById('birthDate').value);
    formData.append('gender', document.getElementById('gender').value);
    formData.append('marital_status', document.getElementById('maritalStatus').value);
    formData.append('number_of_children', document.getElementById('numberOfChildren').value || 0);
    formData.append('phone', document.getElementById('phone').value);
    formData.append('city', document.getElementById('city').value);
    formData.append('salary', document.getElementById('salary').value);
    formData.append('cnps', document.getElementById('cnpsNumber').value);

    // Champ optionnel: commune
    if (document.getElementById('commune').value) {
        formData.append('commune', document.getElementById('commune').value);
    }

    if (currentUser?.id) {
        formData.append('user', currentUser.id);
    }

    // Ajouter les fichiers s'ils sont sélectionnés
    const photoInput = document.getElementById('photo');
    if (photoInput.files[0]) {
        formData.append('photo', photoInput.files[0]);
    }

    const cniInput = document.getElementById('cniDocument');
    if (cniInput.files[0]) {
        formData.append('cni_document', cniInput.files[0]);
    }

    console.log('Envoi du formulaire avec fichiers');

    const submitBtn = document.querySelector('#employeeProfileForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';
    submitBtn.disabled = true;

    try {
        let response;
        const employeeId = document.getElementById('employeeId').value;

        if (employeeId) {
            // Mise à jour avec fichiers
            response = await apiPutFormData(API_ENDPOINTS.EMPLOYEE_DETAIL(employeeId), formData);
        } else {
            // Création avec fichiers
            response = await apiPostFormData(API_ENDPOINTS.EMPLOYEES, formData);
        }

        if (response.ok) {
            currentEmployee = response.data;
            displayProfile(currentEmployee);
            showNotification('Profil enregistré avec succès !', 'success');
            switchSection('profile');
        } else {
            const errorMsg = response.data?.email?.[0] || response.data?.detail || 'Erreur lors de l\'enregistrement';
            showNotification(errorMsg, 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur de connexion au serveur', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

async function handleLeaveSubmit(e) {
    e.preventDefault();

    if (!currentEmployee) {
        showNotification('Veuillez d\'abord compléter votre profil', 'error');
        return;
    }

    const formData = {
        employee: currentEmployee.id,
        leave_type: document.getElementById('leaveType').value,
        start_date: document.getElementById('leaveStartDate').value,
        end_date: document.getElementById('leaveEndDate').value,
        reason: document.getElementById('leaveReason').value || ''
    };

    // Validation des dates
    if (new Date(formData.end_date) < new Date(formData.start_date)) {
        showNotification('La date de fin doit être après la date de début', 'error');
        return;
    }

    // Validation du solde de congés (uniquement pour les congés payés)
    if (formData.leave_type === 'paid') {
        const daysRequested = calculateDays(formData.start_date, formData.end_date);
        const balance = currentEmployee.leave_balance ?? 30;
        const pending = currentEmployee.leaves_pending_this_year ?? 0;
        const effectiveBalance = balance - pending;

        if (daysRequested > effectiveBalance) {
            showNotification(
                `Solde insuffisant ! Vous avez ${balance} jours disponibles ` +
                `(${pending} en attente). Vous demandez ${daysRequested} jours.`,
                'error'
            );
            return;
        }
    }

    const submitBtn = document.querySelector('#leaveRequestForm button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Envoi...';
    submitBtn.disabled = true;

    try {
        const response = await apiPost(API_ENDPOINTS.LEAVES, formData);

        if (response.ok) {
            showNotification('Demande de congé soumise avec succès !', 'success');
            document.getElementById('leaveRequestForm').reset();
            // Recharger le profil pour mettre à jour le solde de congés
            await loadEmployeeProfile();
            await loadEmployeeLeaves();
            switchSection('leaves');
        } else {
            const errorMsg = response.data?.detail || response.data?.end_date?.[0] || 'Erreur lors de la soumission';
            showNotification(errorMsg, 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur de connexion au serveur', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

function handleLogout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    sessionStorage.removeItem('currentUser');
    window.location.href = 'login.html';
}

// ===========================
// Fonctions utilitaires
// ===========================

function formatDate(dateStr) {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('fr-FR').format(amount) + ' FCFA';
}

function calculateDays(startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const diffTime = Math.abs(end - start);
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1;
}

/**
 * Calcule l'âge à partir de la date de naissance
 * @param {string} birthDate - La date de naissance au format YYYY-MM-DD
 * @returns {number} - L'âge en années
 */
function calculateAge(birthDate) {
    if (!birthDate) return null;
    const today = new Date();
    const birth = new Date(birthDate);
    let age = today.getFullYear() - birth.getFullYear();
    const monthDiff = today.getMonth() - birth.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
        age--;
    }
    return age;
}

/**
 * Calcule l'année de départ à la retraite (60 ans)
 * @param {string} birthDate - La date de naissance au format YYYY-MM-DD
 * @returns {number|null} - L'année de retraite
 */
function calculateRetirementYear(birthDate) {
    if (!birthDate) return null;
    const birth = new Date(birthDate);
    return birth.getFullYear() + 60;
}

/**
 * Valide l'âge de l'employé (18-60 ans)
 * @param {string} birthDate - La date de naissance
 * @returns {object} - { valid: boolean, message: string, age: number }
 */
function validateEmployeeAge(birthDate) {
    const age = calculateAge(birthDate);
    if (age === null) {
        return { valid: false, message: 'Veuillez entrer une date de naissance', age: null };
    }
    if (age < 18) {
        return { valid: false, message: `L'employé doit avoir au moins 18 ans (âge actuel: ${age} ans)`, age };
    }
    if (age >= 60) {
        return { valid: false, message: `L'employé doit avoir moins de 60 ans (âge actuel: ${age} ans)`, age };
    }
    return { valid: true, message: '', age };
}

function getDepartmentName(deptId) {
    const dept = departments.find(d => d.id === deptId);
    return dept?.name || '-';
}

function getMaritalStatusLabel(status) {
    const labels = {
        'single': 'Célibataire',
        'married': 'Marié(e)',
        'divorced': 'Divorcé(e)',
        'widowed': 'Veuf/Veuve'
    };
    return labels[status] || status;
}

function getGenderLabel(gender) {
    const labels = {
        'male': 'Masculin',
        'female': 'Féminin'
    };
    return labels[gender] || gender;
}

function getLeaveTypeLabel(type) {
    const labels = {
        'paid': 'Congé Payé',
        'sick': 'Congé Maladie',
        'unpaid': 'Sans Solde',
        'parental': 'Parental',
        'other': 'Autre'
    };
    return labels[type] || type;
}

function getStatusLabel(status) {
    const labels = {
        'pending': 'En attente',
        'approved': 'Approuvé',
        'rejected': 'Rejeté'
    };
    return labels[status] || status;
}

function showNotification(message, type = 'info') {
    const existing = document.querySelector('.profile-notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `profile-notification ${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        z-index: 9999;
        animation: slideIn 0.3s ease;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        display: flex;
        align-items: center;
        gap: 0.75rem;
        max-width: 400px;
    `;

    const styles = {
        success: { bg: '#d1fae5', color: '#059669', border: '#10b981', icon: 'check-circle' },
        error: { bg: '#fee2e2', color: '#dc2626', border: '#ef4444', icon: 'exclamation-circle' },
        info: { bg: '#dbeafe', color: '#2563eb', border: '#3b82f6', icon: 'info-circle' }
    };

    const style = styles[type] || styles.info;
    notification.style.background = style.bg;
    notification.style.color = style.color;
    notification.style.border = `1px solid ${style.border}`;
    notification.innerHTML = `<i class="fas fa-${style.icon}"></i> ${message}`;

    document.body.appendChild(notification);

    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// ===========================
// Génération du PDF du profil
// ===========================

async function generateProfilePDF() {
    if (!currentEmployee) {
        showNotification('Aucun profil à télécharger', 'error');
        return;
    }

    // Afficher un indicateur de chargement
    const downloadBtn = document.getElementById('downloadProfileBtn');
    const originalBtnText = downloadBtn.innerHTML;
    downloadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Génération...';
    downloadBtn.disabled = true;

    try {
        // Récupérer jsPDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF();

        // Configuration
        const pageWidth = doc.internal.pageSize.getWidth();
        const margin = 20;
        let y = 20;

        // Couleurs
        const primaryColor = [196, 69, 54]; // Terracotta
        const darkColor = [30, 30, 30];
        const grayColor = [100, 100, 100];

        // En-tête
        doc.setFillColor(...primaryColor);
        doc.rect(0, 0, pageWidth, 40, 'F');

        doc.setTextColor(255, 255, 255);
        doc.setFontSize(24);
        doc.setFont('helvetica', 'bold');
        doc.text('FICHE EMPLOYÉ', pageWidth / 2, 25, { align: 'center' });

        y = 55;

        // Photo de l'employé (si disponible)
        const fullName = currentEmployee.full_name || `${currentEmployee.first_name} ${currentEmployee.last_name}`;

        if (currentEmployee.photo) {
            try {
                // Charger l'image et la convertir en base64
                const imgData = await loadImageAsBase64(currentEmployee.photo);
                if (imgData) {
                    // Ajouter la photo (centrée, taille 35x45 mm - format photo d'identité)
                    const photoWidth = 35;
                    const photoHeight = 45;
                    const photoX = (pageWidth - photoWidth) / 2;

                    // Ajouter un cadre blanc autour de la photo
                    doc.setFillColor(255, 255, 255);
                    doc.roundedRect(photoX - 2, y - 2, photoWidth + 4, photoHeight + 4, 2, 2, 'F');

                    // Ajouter l'image
                    doc.addImage(imgData, 'JPEG', photoX, y, photoWidth, photoHeight);

                    y += photoHeight + 10;
                }
            } catch (photoError) {
                console.error('Erreur chargement photo:', photoError);
                // Continuer sans la photo si elle ne peut pas être chargée
            }
        }

        // Nom de l'employé
        doc.setTextColor(...darkColor);
        doc.setFontSize(18);
        doc.setFont('helvetica', 'bold');
        doc.text(fullName, pageWidth / 2, y, { align: 'center' });
        y += 10;

        doc.setFontSize(12);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...grayColor);
        doc.text(currentEmployee.position || 'Poste non défini', pageWidth / 2, y, { align: 'center' });
        y += 20;

        // Fonction pour ajouter une section
        function addSection(title, data) {
            // Titre de section
            doc.setFillColor(...primaryColor);
            doc.rect(margin, y, pageWidth - 2 * margin, 8, 'F');
            doc.setTextColor(255, 255, 255);
            doc.setFontSize(11);
            doc.setFont('helvetica', 'bold');
            doc.text(title, margin + 3, y + 6);
            y += 12;

            // Données
            doc.setTextColor(...darkColor);
            doc.setFontSize(10);
            doc.setFont('helvetica', 'normal');

            data.forEach(item => {
                doc.setFont('helvetica', 'bold');
                doc.text(item.label + ' :', margin, y);
                doc.setFont('helvetica', 'normal');
                doc.text(item.value || '-', margin + 55, y);
                y += 7;
            });

            y += 5;
        }

        // Section: Informations personnelles
        const age = calculateAge(currentEmployee.birth_date);
        const retirementYear = calculateRetirementYear(currentEmployee.birth_date);
        addSection('INFORMATIONS PERSONNELLES', [
            { label: 'Nom complet', value: fullName },
            { label: 'Date de naissance', value: formatDate(currentEmployee.birth_date) },
            { label: 'Âge actuel', value: age ? `${age} ans` : '-' },
            { label: 'Sexe', value: getGenderLabel(currentEmployee.gender) || '-' },
            { label: 'Situation matrimoniale', value: getMaritalStatusLabel(currentEmployee.marital_status) },
            { label: 'Nombre d\'enfants', value: String(currentEmployee.number_of_children || 0) },
            { label: 'Année de retraite', value: retirementYear ? String(retirementYear) : '-' }
        ]);

        // Section: Coordonnées
        addSection('COORDONNÉES', [
            { label: 'Email', value: currentEmployee.email },
            { label: 'Téléphone', value: currentEmployee.phone },
            { label: 'Ville', value: currentEmployee.city },
            { label: 'Commune', value: currentEmployee.commune }
        ]);

        // Section: Informations professionnelles
        const deptName = currentEmployee.department_name || getDepartmentName(currentEmployee.department);
        addSection('INFORMATIONS PROFESSIONNELLES', [
            { label: 'Entreprise', value: deptName },
            { label: 'Poste', value: currentEmployee.position },
            { label: 'Date d\'embauche', value: formatDate(currentEmployee.hire_date) },
            { label: 'Salaire', value: currentEmployee.salary ? formatCurrency(currentEmployee.salary) : '-' },
            { label: 'Numéro CNPS', value: currentEmployee.cnps }
        ]);

        // Section: Congés
        addSection('SITUATION CONGÉS', [
            { label: 'Quota annuel', value: '30 jours' },
            { label: 'Jours pris', value: String(currentEmployee.leaves_taken_this_year || 0) + ' jours' },
            { label: 'Jours restants', value: String(currentEmployee.leave_balance || 30) + ' jours' }
        ]);

        // Pied de page
        const today = new Date().toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: 'long',
            year: 'numeric'
        });

        doc.setFontSize(9);
        doc.setTextColor(...grayColor);
        doc.text(`Document généré le ${today}`, margin, 280);
        doc.text('EmpManager - Système de Gestion du Personnel', pageWidth - margin, 280, { align: 'right' });

        // Télécharger le PDF
        const fileName = `Profil_${currentEmployee.first_name}_${currentEmployee.last_name}.pdf`;
        doc.save(fileName);

        showNotification('Profil téléchargé avec succès !', 'success');
    } catch (error) {
        console.error('Erreur génération PDF:', error);
        showNotification('Erreur lors de la génération du PDF', 'error');
    } finally {
        // Restaurer le bouton
        downloadBtn.innerHTML = originalBtnText;
        downloadBtn.disabled = false;
    }
}

/**
 * Charge une image depuis une URL et la convertit en base64
 * @param {string} url - L'URL de l'image
 * @returns {Promise<string|null>} - L'image en base64 ou null en cas d'erreur
 */
function loadImageAsBase64(url) {
    return new Promise((resolve) => {
        const img = new Image();
        img.crossOrigin = 'Anonymous';

        img.onload = function() {
            try {
                const canvas = document.createElement('canvas');
                canvas.width = img.width;
                canvas.height = img.height;

                const ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0);

                const dataURL = canvas.toDataURL('image/jpeg', 0.8);
                resolve(dataURL);
            } catch (e) {
                console.error('Erreur conversion image:', e);
                resolve(null);
            }
        };

        img.onerror = function() {
            console.error('Erreur chargement image:', url);
            resolve(null);
        };

        // Ajouter un timestamp pour éviter le cache
        const separator = url.includes('?') ? '&' : '?';
        img.src = url + separator + 't=' + Date.now();
    });
}

// Animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
`;
document.head.appendChild(style);
