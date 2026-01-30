from django.contrib import admin
from .models import Department, Employee, Leave, Attendance


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'manager', 'employees_count', 'created_at']
    search_fields = ['name', 'manager']
    list_filter = ['created_at']
    ordering = ['name']


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'email', 'department', 'position', 'status', 'hire_date']
    search_fields = ['first_name', 'last_name', 'email', 'cnps']
    list_filter = ['status', 'department', 'hire_date']
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Informations personnelles', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'address')
        }),
        ('Informations professionnelles', {
            'fields': ('department', 'position', 'hire_date', 'salary', 'cnps', 'status')
        }),
        ('Compte utilisateur', {
            'fields': ('user',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ['employee', 'leave_type', 'start_date', 'end_date', 'days_count', 'status', 'created_at']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    list_filter = ['status', 'leave_type', 'start_date']
    ordering = ['-created_at']
    list_per_page = 25

    fieldsets = (
        ('Employé', {
            'fields': ('employee',)
        }),
        ('Détails du congé', {
            'fields': ('leave_type', 'start_date', 'end_date', 'reason')
        }),
        ('Approbation', {
            'fields': ('status', 'approved_by')
        }),
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['employee', 'date', 'check_in', 'check_out', 'hours_worked', 'status']
    search_fields = ['employee__first_name', 'employee__last_name']
    list_filter = ['status', 'date']
    ordering = ['-date']
    list_per_page = 25

    fieldsets = (
        ('Employé', {
            'fields': ('employee', 'date')
        }),
        ('Pointage', {
            'fields': ('check_in', 'check_out', 'status')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
