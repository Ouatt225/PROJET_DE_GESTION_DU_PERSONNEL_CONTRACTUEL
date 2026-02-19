// ===========================
// Téléchargement du profil employé en PDF
// ===========================

async function downloadEmployeeProfile(employeeId) {
    const employee = AppState.employees.find(e => e.id === employeeId);

    if (!employee) {
        alert('Employé non trouvé');
        return;
    }

    try {
        const fullEmployee = await apiGet(API_ENDPOINTS.EMPLOYEE_DETAIL(employeeId));
        await generateEmployeePDF(fullEmployee || employee);
    } catch (error) {
        console.error('Erreur:', error);
        await generateEmployeePDF(employee);
    }
}

async function generateEmployeePDF(employee) {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();

    const pageWidth = 210;
    const marginL = 10;
    const contentW = 190;
    let y = 10;
    const rowH = 10;

    const green = [56, 118, 29];
    const valueColor = [56, 142, 60];
    const border = [180, 180, 180];
    const black = [0, 0, 0];

    function calculateAge(birthDate) {
        if (!birthDate) return null;
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const m = today.getMonth() - birth.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
        return age;
    }

    function calculateRetirementYear(birthDate) {
        if (!birthDate) return null;
        return new Date(birthDate).getFullYear() + 60;
    }

    function calcRetirementDate(bd) {
        if (!bd) return '-';
        const b = new Date(bd);
        const r = new Date(b);
        r.setFullYear(r.getFullYear() + 60);
        return r.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    }

    function formatCurrency(amount) {
        if (!amount) return '-';
        return new Intl.NumberFormat('fr-FR').format(amount) + ' FCFA';
    }

    function getMaritalStatusLabel(status) {
        const labels = { 'single': 'Célibataire', 'married': 'Marié(e)', 'divorced': 'Divorcé(e)', 'widowed': 'Veuf/Veuve' };
        return labels[status] || status || '-';
    }

    function getGenderLabel(gender) {
        const labels = { 'male': 'Masculin', 'female': 'Féminin' };
        return labels[gender] || gender || '-';
    }

    function getEmployeeStatusLabel(status) {
        const labels = { 'active': 'Présent et Payé', 'inactive': 'Absent', 'on_leave': 'En Congé' };
        return labels[status] || status || '-';
    }

    function loadImageAsBase64PDF(url) {
        return new Promise((resolve) => {
            const img = new Image();
            img.crossOrigin = 'Anonymous';
            img.onload = function() {
                try {
                    const canvas = document.createElement('canvas');
                    canvas.width = img.width;
                    canvas.height = img.height;
                    canvas.getContext('2d').drawImage(img, 0, 0);
                    resolve(canvas.toDataURL('image/jpeg', 0.8));
                } catch (e) { resolve(null); }
            };
            img.onerror = function() { resolve(null); };
            const sep = url.includes('?') ? '&' : '?';
            img.src = url + sep + 't=' + Date.now();
        });
    }

    function clean(str) {
        return String(str || '-').replace(/[\u00A0\u202F\u2009\u200B]/g, ' ');
    }

    function drawSectionHeader(title) {
        if (y > 270) { doc.addPage(); y = 10; }
        doc.setFillColor(...green);
        doc.rect(marginL, y, contentW, 12, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('  ' + title, marginL + 3, y + 8.5);
        y += 12;
    }

    function drawInfoRow(label, value, labelW, totalW) {
        if (y > 280) { doc.addPage(); y = 10; }
        doc.setDrawColor(...border);
        doc.setLineWidth(0.3);
        doc.rect(marginL, y, labelW, rowH);
        doc.setTextColor(...black);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(label + ' :', marginL + 3, y + 7);
        doc.rect(marginL + labelW, y, totalW - labelW, rowH);
        doc.setTextColor(...valueColor);
        doc.setFont('helvetica', 'normal');
        doc.text(clean(value).toUpperCase(), marginL + labelW + 3, y + 7);
        y += rowH;
    }

    function fitValue(text, maxW) {
        doc.setFontSize(10);
        if (doc.getTextWidth(text) <= maxW) return;
        doc.setFontSize(8);
        if (doc.getTextWidth(text) <= maxW) return;
        doc.setFontSize(7);
    }

    function drawOneColRow(label, value) {
        if (y > 280) { doc.addPage(); y = 10; }
        const lw = 45;
        const maxValW = contentW - lw - 3;
        doc.setDrawColor(...border);
        doc.setLineWidth(0.3);
        doc.rect(marginL, y, contentW, rowH);
        doc.setTextColor(...black);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(label + ' :', marginL + 3, y + 7);
        doc.setTextColor(...valueColor);
        doc.setFont('helvetica', 'normal');
        let v = clean(value).toUpperCase();
        fitValue(v, maxValW);
        doc.text(v, marginL + lw, y + 7, { maxWidth: maxValW });
        doc.setFontSize(10);
        y += rowH;
    }

    function drawTwoColRow(label1, value1, label2, value2) {
        if (y > 280) { doc.addPage(); y = 10; }
        const halfW = contentW / 2;
        const lw = 45;
        const maxValW = halfW - lw - 3;
        doc.setDrawColor(...border);
        doc.setLineWidth(0.3);

        doc.rect(marginL, y, halfW, rowH);
        doc.setTextColor(...black);
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(label1 + ' :', marginL + 3, y + 7);
        doc.setTextColor(...valueColor);
        doc.setFont('helvetica', 'normal');
        let v1 = clean(value1).toUpperCase();
        fitValue(v1, maxValW);
        doc.text(v1, marginL + lw, y + 7, { maxWidth: maxValW });
        doc.setFontSize(10);

        doc.rect(marginL + halfW, y, halfW, rowH);
        if (label2) {
            doc.setTextColor(...black);
            doc.setFont('helvetica', 'bold');
            doc.text(label2 + ' :', marginL + halfW + 3, y + 7);
            doc.setTextColor(...valueColor);
            doc.setFont('helvetica', 'normal');
            let v2 = clean(value2).toUpperCase();
            fitValue(v2, maxValW);
            doc.text(v2, marginL + halfW + lw, y + 7, { maxWidth: maxValW });
            doc.setFontSize(10);
        } else {
            doc.setTextColor(...valueColor);
            doc.text('-', marginL + halfW + 3, y + 7);
        }
        y += rowH;
    }

    // === INFORMATIONS GÉNÉRALES ===
    drawSectionHeader('INFORMATIONS GÉNÉRALES');

    const infoLabelW = 48;
    const infoTotalW = 120;
    const photoAreaX = marginL + infoTotalW;
    const photoAreaW = contentW - infoTotalW;
    const infoStartY = y;

    const matricule = employee.matricule || '-';
    const fullName = `${employee.first_name || ''} ${employee.last_name || ''}`.trim();
    const birthDate = employee.birth_date || employee.birthDate;
    const age = calculateAge(birthDate);
    const retirementYear = calculateRetirementYear(birthDate);

    drawInfoRow('Matricule', matricule, infoLabelW, infoTotalW);
    drawInfoRow('Nom et Prénoms', fullName, infoLabelW, infoTotalW);
    drawInfoRow('Date de Naissance', formatDate(birthDate), infoLabelW, infoTotalW);
    drawInfoRow('Lieu de Naissance', employee.birth_place || '-', infoLabelW, infoTotalW);
    drawInfoRow('Âge actuel', age ? `${age} ans` : '-', infoLabelW, infoTotalW);
    drawInfoRow('Année de Retraite', retirementYear || '-', infoLabelW, infoTotalW);

    const infoEndY = y;
    doc.setDrawColor(...border);
    doc.setLineWidth(0.3);
    doc.rect(photoAreaX, infoStartY, photoAreaW, infoEndY - infoStartY);

    if (employee.photo) {
        try {
            const imgData = await loadImageAsBase64PDF(employee.photo);
            if (imgData) {
                const photoW = 35;
                const photoH = 40;
                const photoX = photoAreaX + (photoAreaW - photoW) / 2;
                const photoY = infoStartY + 2;
                doc.addImage(imgData, 'JPEG', photoX, photoY, photoW, photoH);
                doc.setTextColor(...black);
                doc.setFontSize(9);
                doc.setFont('helvetica', 'bold');
                doc.text(String(matricule), photoAreaX + photoAreaW / 2, infoEndY - 2, { align: 'center' });
            }
        } catch (e) {
            console.error('Erreur chargement photo:', e);
        }
    }

    y += 5;

    drawTwoColRow('Sexe', getGenderLabel(employee.gender), 'Email', employee.email);
    drawTwoColRow('Numéro CNPS', employee.cnps, 'Commune', employee.commune);
    drawTwoColRow('Téléphone', employee.phone, "Nombre d'enfant", employee.number_of_children);
    drawTwoColRow('Ville', employee.city, null, null);
    drawTwoColRow('Situation Famille', getMaritalStatusLabel(employee.marital_status || employee.maritalStatus), null, null);

    y += 5;

    // === EMPLOI ===
    drawSectionHeader('EMPLOI');
    const deptName = employee.department_name || employee.department;
    drawTwoColRow('Entreprise', deptName, "Date d'embauche", formatDate(employee.hire_date || employee.hireDate));
    drawOneColRow('Direction', employee.direction);
    drawTwoColRow('Salaire', formatCurrency(employee.salary), 'Lieu de Travail', employee.city);
    drawTwoColRow('Emploi', employee.position, null, null);

    y += 5;

    // === ETAT AGENT ===
    drawSectionHeader('ETAT AGENT');
    drawTwoColRow('Date prise de service', formatDate(employee.hire_date || employee.hireDate), 'Solde Congés', (employee.leave_balance != null ? employee.leave_balance : 15) + ' jours');
    drawTwoColRow('Date départ retraite', calcRetirementDate(birthDate), 'Congés Pris', (employee.leaves_taken_this_year || 0) + ' jours');
    drawTwoColRow('Etat', getEmployeeStatusLabel(employee.status), null, null);

    const firstName = employee.first_name || employee.firstName || 'Employe';
    const lastName = employee.last_name || employee.lastName || '';
    doc.save(`Fiche_${firstName}_${lastName}.pdf`);
}

window.downloadEmployeeProfile = downloadEmployeeProfile;
