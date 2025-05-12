from django.db import models
from django.db.models import Q

from django.db.models import Q

class VisibilityManager(models.Manager):
    def visible_for_user(self, user):

        if user.is_superuser:
            return self.get_queryset()

        # Agentes del usuario, esto es solo para los usuarios normales (no admins)
        agents_names = list(user.agent_seguro.values_list('name', flat=True))

        # Filtrar por compañía y agentes en 'agent_seguro'
        company_filter = Q(company_id=user.company_id)
        usa_filter = Q(agent_usa__in=agents_names)

        # Si el usuario es Admin y está en el 'agent_seguro', mostramos todo
        if user.role == 'Admin' and agents_names:
            # Mostrar ventas de su compañía + las de los agentes en 'agent_seguro', sin importar la compañía
            return self.get_queryset().filter(company_filter | usa_filter)

        # Si el usuario no es Admin o no está en 'agent_seguro', solo filtra por compañía
        return self.get_queryset().filter(company_filter)




