from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DirectionViewSet, PasswordRecordViewSet, DepartmentViewSet, EmployeeViewSet,
    LeaveViewSet, AttendanceViewSet,
    RegisterView, LoginView, ChangePasswordView, DashboardStatsView,
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
