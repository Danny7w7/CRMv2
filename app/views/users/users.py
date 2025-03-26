# Standard Python libraries
from django.http import JsonResponse, HttpResponse

# Django core libraries
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render 

# Application-specific imports
from app.models import *

from ..decoratorsCompany import *

@company_ownership_required_sinURL
@login_required(login_url='/login') 
def formCreateUser(request, company_id):

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
@company_ownership_required_sinURL
def editUser(request, company_id, user_id):
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
def toggleUser(request, user_id):
    # Obtener el cliente por su ID
    user = get_object_or_404(Users, id=user_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    user.is_active = not user.is_active
    user.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('formCreateUser')
