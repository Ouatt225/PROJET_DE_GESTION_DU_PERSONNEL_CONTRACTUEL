@echo off
echo ========================================
echo Configuration du backend EmpManager
echo ========================================
echo.

echo 1. Creation de l'environnement virtuel...
python -m venv venv
call venv\Scripts\activate

echo.
echo 2. Installation des dependances...
pip install -r requirements.txt

echo.
echo 3. Application des migrations...
python manage.py makemigrations
python manage.py migrate

echo.
echo 4. Creation du superutilisateur...
echo.
echo Utilisateurs de demonstration :
echo - Admin: admin / admin123
echo - Manager: manager / manager123
echo - Employe: employee / employee123
echo.

python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@empmanager.com', 'admin123') if not User.objects.filter(username='admin').exists() else None; User.objects.create_user('manager', 'manager@empmanager.com', 'manager123', is_staff=True) if not User.objects.filter(username='manager').exists() else None; User.objects.create_user('employee', 'employee@empmanager.com', 'employee123') if not User.objects.filter(username='employee').exists() else None; print('Utilisateurs crees avec succes!')"

echo.
echo ========================================
echo Configuration terminee avec succes!
echo ========================================
echo.
echo Pour demarrer le serveur, executez :
echo python manage.py runserver
echo.
pause
