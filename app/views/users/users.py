# Standard Python libraries
from datetime import timedelta
import datetime
import json
import stripe 
from django.http import JsonResponse, HttpResponse

# Django core libraries
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render

from django.conf import settings
# Application-specific imports
from app.models import *
from app.modelsSMS import *

from ..decoratorsCompany import *

@login_required(login_url='/login') 
@company_ownership_required_sinURL
@staffUserRequired
def formCreateUser(request):

    company_id = request.company_id  # Obtener company_id desde request

    if request.user.is_superuser:
        users = Users.objects.exclude(is_superuser = True)
        companies = Companies.objects.filter(is_active = True)
    else:
        users = Users.objects.filter(company = company_id, is_active = True).exclude(is_superuser = True)
        companies = Companies.objects.filter(id = company_id, is_active = True).first()

    roles = Users.ROLES_CHOICES  # Obtén las opciones dinámicamente desde el modelo

    if request.method == 'POST':
        first_name = request.POST.get('first_name').upper()
        last_name = request.POST.get('last_name').upper()
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role')
        company = request.POST.get('company')
        
        try:
            # Validar si el username ya existe
            if Users.objects.filter(username=username).exists():
                return render(request, 'forms/formCreateUser.html', {'msg':f'El nombre de usuario "{username}" ya está en uso.','users':users, 'type':'error'})
            
            # Obtener la instancia/objeto Company
            company = companies.filter(id=company).first()

            # Crear el usuario si no existe el username
            user = Users.objects.create(
                username=username,
                password=make_password(password),  # Encriptar la contraseña
                last_name=last_name,
                first_name=first_name,
                role=role,
                company = company
            )

            context = {
                'msg':f'Usuario {user.username} creado con éxito.',
                'users':users,
                'type':'good',
                'roles': roles,
                'companies' : companies
            }

            return render(request, 'forms/formCreateUser.html', context)

        except Exception as e:
            return HttpResponse(str(e))
        
    context = {
            'users':users,
            'roles': roles,
            'companies' : companies
        }
            
    return render(request, 'forms/formCreateUser.html', context)

@login_required(login_url='/login') 
@company_ownership_required(model_name="Users", id_field="user_id")
@staffUserRequired
def editUser(request, user_id):
    # Obtener el usuario a editar o devolver un 404 si no existe
    user = Users.objects.select_related('company').filter(id=user_id).exclude(is_superuser=True).first()


    if request.method == 'POST':
        # Recuperar los datos del formulario
        first_name = request.POST.get('first_name', user.first_name)
        last_name = request.POST.get('last_name', user.last_name)
        username = request.POST.get('username', user.username)
        role = request.POST.get('role', user.role)
        is_active = request.POST.get('is_active', user.is_active)

        # Verificar si el nuevo username ya existe en otro usuario
        if username != user.username and Users.objects.filter(username=username).exists():
            return JsonResponse({'error': f'El nombre de usuario "{username}" ya está en uso.'}, status=400)

        # Actualizar los datos del usuario
        user.first_name = first_name
        user.last_name = last_name
        user.username = username
        user.role = role
        user.is_active = is_active

        # Guardar los cambios
        user.save()

        # Redirigir a otra vista o mostrar un mensaje de éxito
        return redirect('formCreateUser')  

    # Renderizar el formulario con los datos actuales del usuario
    context = {'users': user}
    return render(request, 'edit/editUser.html', context)

@login_required(login_url='/login')
@staffUserRequired
def toggleUser(request, user_id):
    # Obtener el cliente por su ID
    user = get_object_or_404(Users, id=user_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    user.is_active = not user.is_active
    user.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('formCreateUser')

def assignModulesModal(request, company_id):
    # Obtén la compañía por el ID recibido
    company = get_object_or_404(Companies, pk=company_id) # Usa 'Companies' aquí

    all_modules = Module.objects.all()
    selected_modules = company.modules.all() # Módulos ya asignados a esta compañía

    if request.method == 'POST':
        selected_ids = request.POST.getlist('modules')
        
        try:
            modules_to_assign = Module.objects.filter(id__in=selected_ids)
            company.modules.set(modules_to_assign) # Asigna a la compañía
            # CAMBIO AQUÍ: usa company.company_name
            return JsonResponse({'status': 'success', 'message': f'Módulos asignados correctamente a la compañía {company.company_name}.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error al guardar los módulos: {str(e)}'}, status=500)

    # Si es GET, renderiza el formulario
    context = {
        'modules': all_modules,
        'selected_modules': selected_modules,
        'company_id': company_id,
        'company_obj': company # Esto sigue siendo útil para la plantilla
    }
    return render(request, 'auth/assignModules.html', context)

@user_passes_test(lambda u: u.is_superuser or u.role == 'Admin')
@login_required(login_url='/login') 
@staffUserRequired
def userModule(request):
    
    company = Companies.objects.all()

    return render(request, 'auth/userModule.html', {'company' : company})