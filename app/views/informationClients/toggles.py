# Django core libraries
from django.shortcuts import get_object_or_404, redirect
 
# Application-specific imports
from app.models import *

def toggleObamaStatus(request, obamacare_id):
    # Obtener el cliente por su ID
    obama = get_object_or_404(ObamaCare, id=obamacare_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    obama.is_active = not obama.is_active
    obama.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('clientObamacare')

def toggleSuppStatus(request, supp_id):
    # Obtener el cliente por su ID
    supp = get_object_or_404(Supp, id=supp_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    supp.is_active = not supp.is_active
    supp.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('clientSupp')

def toggleAlert(request, alertClient_id):
    # Obtener el cliente por su ID
    alert = get_object_or_404(ClientAlert, id=alertClient_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    alert.is_active = not alert.is_active
    alert.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('alert')

def toggleTypification(request, typifications_id):
    # Obtener el cliente por su ID
    typi = get_object_or_404(ObservationCustomer, id=typifications_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    typi.is_active = not typi.is_active
    typi.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('typification')

def toggleTicketStatus(ticket_id):
    
    # Obtener el cliente por su ID
    ticket = get_object_or_404(AgentTicketAssignment, id=ticket_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    ticket.is_active = not ticket.is_active
    ticket.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('ticketAsing')

def toggleAssureStatus(request,assure_id):
    
    # Obtener el cliente por su ID
    assure = get_object_or_404(ClientsAssure, id=assure_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    assure.is_active = not assure.is_active
    assure.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('clientAssure')

def toggleLifeStatus(request,client_id):
    
    # Obtener el cliente por su ID
    client = get_object_or_404(ClientsLifeInsurance, id=client_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    client.is_active = not client.is_active
    client.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('clientLifeInsurance')



