from django.shortcuts import render
from django.http import HttpResponseForbidden
from app.models import * # Ajusta las importaciones
from functools import wraps
from django.shortcuts import render
from django.apps import apps  # Para obtener modelos dinámicamente
from django.core.exceptions import PermissionDenied
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect

def company_ownership_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, company_id, *args, **kwargs):
        try:
            requested_company_id = int(company_id)
        except ValueError:
            return HttpResponseForbidden("ID de compañía inválido.")

        if request.user.is_authenticated:
            try:
                user = Users.objects.get(id=request.user.id)
                user_company_id = user.company.id
            except Users.DoesNotExist:
                return HttpResponseForbidden("Perfil de usuario no encontrado.")
        else:
            return HttpResponseForbidden("Acceso no autorizado.")

        if requested_company_id != user_company_id:
            return HttpResponseForbidden("No estás autorizado a ver información de esta compañía.")
        else:
            return view_func(request, company_id, *args, **kwargs)
    return _wrapped_view

def company_ownership_required_sinURL(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return render(request, "auth/404.html", {"message": "Acceso no autorizado."})

        if request.user.is_superuser:
            request.company_id = 1  # O un valor por defecto si es necesario
        else:
            try:
                user = Users.objects.select_related('company').get(id=request.user.id)
                request.company_id = user.company.id  # Asignar el ID de la compañía al request
            except Users.DoesNotExist:
                return render(request, "auth/404.html", {"message": "Perfil de usuario no encontrado."})

        return view_func(request, *args, **kwargs)  

    return _wrapped_view

def company_ownership_required(model_name, id_field, company_field="company_id",  agent_field="agent_usa"):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):

            # Si el usuario es superusuario, permitir acceso total
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            # Obtener el ID dinámicamente desde kwargs
            obj_id = kwargs.get(id_field)
            if obj_id is None:
                return render(request, "auth/404.html", {"message": "ID no encontrado."})

            # Obtener el modelo dinámicamente
            try:
                Model = apps.get_model("app", model_name)  # 🔴 Cambia 'app' por el nombre real de tu app
                obj = Model.objects.get(id=obj_id)
            except ObjectDoesNotExist:
                return render(request, "auth/404.html", {"message": "Registro no encontrado."})

            # Obtener la empresa del objeto
            obj_company_id = getattr(obj, company_field, None)

            # Obtener la empresa del usuario
            user_company_id = getattr(request.user, "company_id", None)

            # ⚠️ Nueva lógica: permitir si está en agent_seguro aunque sea otra compañía
            agent_usa = getattr(obj, agent_field, "")
            related_agents = list(request.user.agent_seguro.values_list("name", flat=True))

            if obj_company_id == user_company_id or agent_usa in related_agents:
                return view_func(request, *args, **kwargs)

            return render(request, "auth/404.html", {"message": "No tienes permiso para acceder a este recurso."})

        return _wrapped_view

    return decorator

def superuserRequired(viewFunc):
    @wraps(viewFunc)
    def _wrappedView(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_superuser:
            return redirect('index')  # Asegúrate de tener definida la URL 'index' en tu archivo urls.py
        return viewFunc(request, *args, **kwargs)
    return _wrappedView

def staffUserRequired(viewFunc):
    @wraps(viewFunc)
    def _wrappedView(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.role == 'Admin':
            return redirect('index')  # Asegúrate de tener definida la URL 'index' en tu archivo urls.py
        return viewFunc(request, *args, **kwargs)
    return _wrappedView