from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import Department, Employee, Leave, Attendance
from .serializers import (
    DepartmentSerializer, EmployeeSerializer,
    LeaveSerializer, AttendanceSerializer,
    RegisterSerializer, UserSerializer
)


class DepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet pour les départements/entreprises"""
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def employees(self, request, pk=None):
        """Récupère tous les employés d'un département"""
        department = self.get_object()
        employees = department.employees.all()
        serializer = EmployeeSerializer(employees, many=True)
        return Response(serializer.data)


class EmployeeViewSet(viewsets.ModelViewSet):
    """ViewSet pour les employés"""
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['department', 'status', 'position']
    search_fields = ['first_name', 'last_name', 'email', 'position']
    ordering_fields = ['created_at', 'hire_date', 'last_name']

    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """Récupère les employés groupés par département"""
        departments = Department.objects.all()
        result = []
        for dept in departments:
            result.append({
                'department': DepartmentSerializer(dept).data,
                'employees': EmployeeSerializer(dept.employees.all(), many=True).data
            })
        return Response(result)


class LeaveViewSet(viewsets.ModelViewSet):
    """ViewSet pour les congés"""
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['employee', 'status', 'leave_type']
    search_fields = ['employee__first_name', 'employee__last_name', 'reason']
    ordering_fields = ['created_at', 'start_date']

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approuve une demande de congé"""
        leave = self.get_object()
        leave.status = 'approved'
        leave.approved_by = request.user
        leave.save()
        serializer = self.get_serializer(leave)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rejette une demande de congé"""
        leave = self.get_object()
        leave.status = 'rejected'
        leave.approved_by = request.user
        leave.save()
        serializer = self.get_serializer(leave)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Récupère toutes les demandes en attente"""
        pending_leaves = self.queryset.filter(status='pending')
        serializer = self.get_serializer(pending_leaves, many=True)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ModelViewSet):
    """ViewSet pour les présences"""
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['employee', 'status', 'date']
    search_fields = ['employee__first_name', 'employee__last_name']
    ordering_fields = ['date']

    @action(detail=False, methods=['get'])
    def today(self, request):
        """Récupère les présences d'aujourd'hui"""
        from datetime import date
        today_attendance = self.queryset.filter(date=date.today())
        serializer = self.get_serializer(today_attendance, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_employee(self, request):
        """Récupère les présences par employé"""
        employee_id = request.query_params.get('employee_id')
        if not employee_id:
            return Response(
                {"error": "employee_id est requis"},
                status=status.HTTP_400_BAD_REQUEST
            )

        attendances = self.queryset.filter(employee_id=employee_id)
        serializer = self.get_serializer(attendances, many=True)
        return Response(serializer.data)


class RegisterView(APIView):
    """Vue pour l'enregistrement d'utilisateurs"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """Vue pour la connexion personnalisée avec rôle"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role', 'employee')

        user = authenticate(username=username, password=password)

        if user is not None:
            # Vérifier le rôle
            if role == 'admin' and not user.is_superuser:
                return Response(
                    {"error": "Vous n'avez pas les droits administrateur"},
                    status=status.HTTP_403_FORBIDDEN
                )
            elif role == 'manager' and not user.is_staff:
                return Response(
                    {"error": "Vous n'avez pas les droits manager"},
                    status=status.HTTP_403_FORBIDDEN
                )

            refresh = RefreshToken.for_user(user)
            return Response({
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'name': user.get_full_name() or user.username,
                    'role': role,
                },
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        else:
            return Response(
                {"error": "Identifiants invalides"},
                status=status.HTTP_401_UNAUTHORIZED
            )


class DashboardStatsView(APIView):
    """Vue pour les statistiques du tableau de bord"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from datetime import date
        from django.db.models import Count

        total_employees = Employee.objects.count()
        total_departments = Department.objects.count()
        present_today = Attendance.objects.filter(
            date=date.today(),
            status='present'
        ).count()
        on_leave_today = Leave.objects.filter(
            start_date__lte=date.today(),
            end_date__gte=date.today(),
            status='approved'
        ).count()

        return Response({
            'total_employees': total_employees,
            'total_departments': total_departments,
            'present_today': present_today,
            'on_leave_today': on_leave_today,
        })
