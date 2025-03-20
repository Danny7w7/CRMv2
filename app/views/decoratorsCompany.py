from django.shortcuts import get_object_or_404
from django.http import HttpResponseForbidden
from app.models import Companies, Users  # Ajusta las importaciones
from functools import wraps

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