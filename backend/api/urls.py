"""
Routage URL de l'API REST du système de gestion du personnel contractuel.

Toutes les routes sont préfixées par /api/ (configuré dans empmanager/urls.py).

Routes automatiques (DefaultRouter) :
    /api/directions/          — Directions (lecture seule)
    /api/passwords/           — Mots de passe chiffrés (admins uniquement)
    /api/departments/         — Entreprises prestataires (CRUD)
    /api/employees/           — Agents contractuels (CRUD)
    /api/leaves/              — Demandes de congé (CRUD + actions approve/reject/pending)
    /api/attendances/         — Pointages de présence (CRUD + actions today/by_employee)

Routes manuelles :
    /api/auth/register/       — Création d'un compte utilisateur
    /api/auth/login/          — Authentification JWT (retourne access + refresh tokens)
    /api/auth/change-password/— Modification du mot de passe authentifié
    /api/dashboard/stats/     — Statistiques du tableau de bord (filtrées par rôle)

Rapports Excel (GET, authentifié, retourne un fichier .xlsx) :
    /api/reports/attendance/  — Rapport de présence
    /api/reports/leaves/      — Rapport des congés
    /api/reports/departments/ — Rapport par entreprise
    /api/reports/complete/    — Rapport RH complet
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DirectionViewSet, PasswordRecordViewSet, DepartmentViewSet, EmployeeViewSet,
    LeaveViewSet, AttendanceViewSet,
    RegisterView, LoginView, ChangePasswordView, DashboardStatsView,
)
from .views_reports import (
    AttendanceReportView, LeavesReportView, DepartmentsReportView, CompleteReportView,
)

router = DefaultRouter()
router.register(r'directions', DirectionViewSet)
router.register(r'passwords', PasswordRecordViewSet)
router.register(r'departments', DepartmentViewSet)
router.register(r'employees', EmployeeViewSet)
router.register(r'leaves', LeaveViewSet)
router.register(r'attendances', AttendanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    # Rapports Excel
    path('reports/attendance/', AttendanceReportView.as_view(), name='report-attendance'),
    path('reports/leaves/', LeavesReportView.as_view(), name='report-leaves'),
    path('reports/departments/', DepartmentsReportView.as_view(), name='report-departments'),
    path('reports/complete/', CompleteReportView.as_view(), name='report-complete'),
]
