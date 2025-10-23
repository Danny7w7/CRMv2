
import json
import requests
from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
from ..models import FacebookAccount, FacebookLead


def facebookConnect(request):
    """Redirige al usuario al OAuth de Facebook para conectar su cuenta/página."""
    client_id = settings.FB_APP_ID
    redirect_uri = f"{settings.SITE_URL}/facebook/callback/"
    # Permisos necesarios para acceso completo a leads
    scope = "pages_show_list,leads_retrieval,pages_manage_metadata,pages_read_engagement,pages_manage_ads"

    fb_url = (
        f"https://www.facebook.com/v19.0/dialog/oauth?client_id={client_id}"
        f"&redirect_uri={redirect_uri}&scope={scope}"
    )
    return redirect(fb_url)


def facebookCallback(request):
    """Callback de OAuth con debugging detallado"""
    code = request.GET.get('code')
    error = request.GET.get('error')
    error_reason = request.GET.get('error_reason')
    error_description = request.GET.get('error_description')
    
    # 🔍 Log detallado de errores de Facebook
    if error:
        print(f"❌ Error de Facebook OAuth:")
        print(f"   - Error: {error}")
        print(f"   - Razón: {error_reason}")
        print(f"   - Descripción: {error_description}")
        
        # Mensajes específicos según el tipo de error
        if error_reason == 'user_denied':
            messages.error(request, '❌ Has cancelado la autorización. Debes aceptar todos los permisos para continuar.')
        elif 'not_eligible' in str(error_description).lower():
            messages.error(
                request, 
                '❌ Tu cuenta no es elegible para usar esta función. '
                'Verifica que seas administrador de la página y que tengas permisos de leads.'
            )
        elif 'temporarily_unavailable' in str(error_description).lower():
            messages.error(request, '⚠️ El servicio de Facebook está temporalmente no disponible. Intenta más tarde.')
        else:
            messages.error(request, f'❌ Error de Facebook: {error_description or error}')
        
        return redirect('facebookDashboard')
    
    if not code:
        messages.error(request, '❌ No se recibió código de autorización.')
        return redirect('facebookDashboard')

    try:
        # Obtener token de acceso
        token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
        params = {
            'client_id': settings.FB_APP_ID,
            'redirect_uri': f"{settings.SITE_URL}/facebook/callback/",
            'client_secret': settings.FB_APP_SECRET,
            'code': code,
        }
        r = requests.get(token_url, params=params, timeout=10)
        data = r.json()
        
        print(f"🔍 Respuesta token: {json.dumps(data, indent=2)}")
        
        if 'error' in data:
            error_info = data['error']
            print(f"❌ Error obteniendo token: {error_info}")
            messages.error(
                request, 
                f"❌ Error de Facebook: {error_info.get('message', 'Error desconocido')}"
            )
            return redirect('facebookDashboard')
        
        short_token = data.get('access_token')
        if not short_token:
            messages.error(request, '❌ No se pudo obtener el token de acceso.')
            return redirect('facebookDashboard')

        # Intercambiar por token de larga duración
        long_token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
        long_params = {
            'grant_type': 'fb_exchange_token',
            'client_id': settings.FB_APP_ID,
            'client_secret': settings.FB_APP_SECRET,
            'fb_exchange_token': short_token
        }
        long_r = requests.get(long_token_url, params=long_params, timeout=10)
        long_data = long_r.json()
        
        print(f"🔍 Respuesta long token: {json.dumps(long_data, indent=2)}")
        
        user_token = long_data.get('access_token', short_token)

        # 🔍 Verificar qué permisos se otorgaron realmente
        debug_url = 'https://graph.facebook.com/v19.0/debug_token'
        debug_params = {
            'input_token': user_token,
            'access_token': f"{settings.FB_APP_ID}|{settings.FB_APP_SECRET}"
        }
        debug_r = requests.get(debug_url, params=debug_params, timeout=10)
        debug_data = debug_r.json()
        
        print(f"🔍 Debug token info:")
        print(json.dumps(debug_data, indent=2))
        
        granted_scopes = debug_data.get('data', {}).get('scopes', [])
        print(f"✅ Permisos otorgados: {granted_scopes}")
        
        # Verificar permisos críticos
        required_scopes = ['pages_show_list', 'leads_retrieval', 'pages_manage_metadata']
        missing_scopes = [s for s in required_scopes if s not in granted_scopes]
        
        if missing_scopes:
            messages.error(
                request,
                f'⚠️ Faltan permisos: {", ".join(missing_scopes)}. '
                f'La app no podrá acceder a los leads sin estos permisos.'
            )
            print(f"⚠️ Permisos faltantes: {missing_scopes}")

        # Obtener páginas
        pages_resp = requests.get(
            'https://graph.facebook.com/v19.0/me/accounts',
            params={
                'access_token': user_token,
                'fields': 'id,name,access_token,tasks'  # tasks muestra los permisos de la página
            },
            timeout=10
        )
        pages_data = pages_resp.json()
        
        print(f"🔍 Respuesta páginas: {json.dumps(pages_data, indent=2)}")
        
        if 'error' in pages_data:
            error_info = pages_data['error']
            print(f"❌ Error obteniendo páginas: {error_info}")
            
            # Mensajes específicos según el código de error
            error_code = error_info.get('code')
            error_msg = error_info.get('message', 'Error desconocido')
            
            if error_code == 190:  # Token inválido
                messages.error(request, '❌ Token de acceso inválido. Intenta reconectar tu cuenta.')
            elif error_code == 200:  # Permiso denegado
                messages.error(
                    request,
                    '❌ Acceso denegado. Asegúrate de ser administrador de al menos una página de Facebook '
                    'y de haber autorizado todos los permisos solicitados.'
                )
            elif error_code == 10:  # Permiso no otorgado
                messages.error(
                    request,
                    '❌ No se otorgaron los permisos necesarios. '
                    'Debes aceptar todos los permisos para que la integración funcione.'
                )
            else:
                messages.error(request, f'❌ Error al obtener páginas: {error_msg}')
            
            return redirect('facebookDashboard')
        
        pages = pages_data.get('data', [])
        
        if not pages:
            messages.warning(
                request,
                '⚠️ No se encontraron páginas. Posibles causas:\n'
                '• No eres administrador de ninguna página\n'
                '• No autorizaste el permiso "pages_show_list"\n'
                '• Tu cuenta no tiene páginas de Facebook'
            )
            return redirect('facebookDashboard')
        
        # Verificar qué páginas tienen acceso a leads
        for page in pages:
            tasks = page.get('tasks', [])
            print(f"📄 Página: {page['name']}")
            print(f"   Tasks: {tasks}")
            
            if 'MANAGE' not in tasks and 'CREATE_CONTENT' not in tasks:
                print(f"   ⚠️ Sin permisos de administración completos")

        return render(request, 'facebook/select_page.html', {
            'pages': pages,
            'user_token': user_token,
            'granted_scopes': granted_scopes,
            'missing_scopes': missing_scopes
        })
        
    except requests.exceptions.Timeout:
        messages.error(request, '⏱️ La solicitud a Facebook tardó demasiado. Intenta nuevamente.')
        return redirect('facebookDashboard')
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de red: {str(e)}")
        messages.error(request, f'❌ Error de conexión: {str(e)}')
        return redirect('facebookDashboard')
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'❌ Error inesperado: {str(e)}')
        return redirect('facebookDashboard')

def subscribePageToApp(page_id, page_access_token):
    """Subscribir la app a la página para recibir webhooks y dar acceso completo."""
    
    # 1. Suscribir la app a los webhooks de leadgen
    subscribe_url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
    subscribe_params = {'access_token': page_access_token}
    subscribe_data = {'subscribed_fields': 'leadgen'}
    
    r1 = requests.post(subscribe_url, params=subscribe_params, data=subscribe_data)
    subscribe_result = r1.json()
    
    print(f"📋 Suscripción webhook: {subscribe_result}")
    
    # 2. Instalar la app en la página (esto da acceso automático)
    install_url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
    install_params = {'access_token': page_access_token}
    install_data = {
        'subscribed_fields': 'leadgen',
        'permissions': 'pages_show_list,leads_retrieval,pages_manage_metadata'
    }
    
    r2 = requests.post(install_url, params=install_params, data=install_data)
    install_result = r2.json()
    
    print(f"📲 Instalación app: {install_result}")
    
    # 3. Asignar permisos de leadgen explícitamente
    permissions_url = f"https://graph.facebook.com/v19.0/{page_id}"
    permissions_params = {'access_token': page_access_token}
    permissions_data = {
        'subscribed_fields': 'leadgen'
    }
    
    r3 = requests.post(permissions_url, params=permissions_params, data=permissions_data)
    
    return {
        'subscribe': subscribe_result,
        'install': install_result,
        'success': subscribe_result.get('success', False)
    }

@csrf_exempt
def facebookSavePage(request):
    """Endpoint para guardar la página seleccionada y redirigir con mensaje de éxito."""
    if request.method != 'POST':
        return HttpResponseBadRequest('Method not allowed')

    payload = request.POST
    owner_name = payload.get('owner_name') or 'Cliente'
    page_id = payload.get('page_id')
    page_name = payload.get('page_name')
    page_token = payload.get('page_access_token')

    if not (page_id and page_token):
        messages.error(request, 'Error: Faltan datos de la página')
        return redirect('facebookDashboard')

    try:
        # Guardar en BD
        fb_acc, created = FacebookAccount.objects.update_or_create(
            page_id=page_id,
            defaults={
                'owner_name': owner_name,
                'page_name': page_name,
                'page_access_token': page_token,
                'is_active': True,
                'company': request.user.company
            }
        )

        # Suscribir la app a la página (para leadgen)
        subscribe_resp = subscribePageToApp(page_id, page_token)
        
        # Verificar si la suscripción fue exitosa
        if subscribe_resp.get('success') or subscribe_resp.get('subscribe', {}).get('success'):
            if created:
                # Agregar instrucciones si es necesario configurar manualmente
                messages.success(
                    request, 
                    f'✅ Página "{page_name}" conectada exitosamente. '
                    f'IMPORTANTE: Si los leads no llegan automáticamente, ve a Meta Business Suite → '
                    f'Configuración de la página → Herramientas de empresa → Aplicaciones conectadas → '
                    f'Agrega "BlueAiW" y activa el acceso a leads.'
                )
            else:
                messages.success(request, f'✅ Página "{page_name}" actualizada correctamente.')
        else:
            messages.warning(request, f'⚠️ Página guardada. Verifica manualmente en Meta Business Suite que la app tenga acceso a leads.')
        
        return redirect('facebookDashboard')
        
    except Exception as e:
        messages.error(request, f'❌ Error al conectar la página: {str(e)}')
        return redirect('facebookDashboard')

def getLeadDetails(leadgen_id, page_access_token):
    """Llama a la Graph API para recuperar el detalle del lead (field_data)."""
    url = f"https://graph.facebook.com/v19.0/{leadgen_id}"
    params = {'access_token': page_access_token}
    r = requests.get(url, params=params)
    return r.json()


@csrf_exempt
def facebookWebhook(request):
    """Webhook único para recibir leads de Facebook."""
    
    # ✅ GET: Verificación inicial de Facebook
    if request.method == 'GET':
        mode = request.GET.get('hub.mode')
        token = request.GET.get('hub.verify_token')
        challenge = request.GET.get('hub.challenge')
        verify_token = getattr(settings, 'FB_VERIFY_TOKEN', None)
        
        print(f"🔍 Verificación webhook")
        print(f"   Mode: {mode}")
        print(f"   Token recibido: '{token}'")
        print(f"   Token esperado: '{verify_token}'")
        print(f"   Challenge: {challenge}")
        
        if mode == 'subscribe' and verify_token and token == verify_token:
            print("✅ Verificación exitosa - Enviando challenge")
            return HttpResponse(challenge, content_type='text/plain')
        else:
            print(f"❌ Verificación fallida")
            if not verify_token:
                print("   ERROR: FB_VERIFY_TOKEN no está configurado en settings")
            elif token != verify_token:
                print(f"   ERROR: Tokens no coinciden")
            return HttpResponse('Invalid verify token', status=403)
    
    # ✅ POST: Recepción de leads
    elif request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            print("📩 Webhook recibido:", json.dumps(body, indent=2))
            
            for entry in body.get('entry', []):
                for change in entry.get('changes', []):
                    if change.get('field') == 'leadgen':
                        page_id = change['value'].get('page_id')
                        leadgen_id = change['value'].get('leadgen_id')
                        
                        print(f"🎯 Lead detectado - Page: {page_id}, Lead ID: {leadgen_id}")
                        
                        fb_account = FacebookAccount.objects.filter(page_id=page_id, is_active=True).first()
                        
                        if fb_account:
                            lead = FacebookLead.objects.create(
                                facebook_account=fb_account,
                                leadgen_id=leadgen_id,
                                raw_payload=change['value'],
                                is_active = True
                            )
                            
                            try:
                                detail = getLeadDetails(leadgen_id, fb_account.page_access_token)
                                lead.raw_payload = detail
                                lead.created_time = detail.get('created_time')
                                lead.save()
                                print(f"✅ Lead {leadgen_id} guardado con detalles")
                            except Exception as e:
                                print(f"⚠️ Error obteniendo detalles del lead: {e}")
                        else:
                            print(f"⚠️ No se encontró FacebookAccount para page_id: {page_id}")
            
            return JsonResponse({'status': 'ok'})
            
        except Exception as e:
            print(f"❌ Error procesando webhook: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return HttpResponseBadRequest('Método no permitido')


def facebookDashboard(request):
    """Dashboard principal con resumen de cuentas y leads"""
    accounts = FacebookAccount.objects.filter(is_active=True, company = request.user.company).annotate(
        total_leads=Count('leads'),
        unprocessed_leads=Count('leads', filter=Q(leads__processed=False))
    ).order_by('-connected_at')
    
    total_accounts = accounts.count()
    total_leads = FacebookLead.objects.select_related('facebook_account').filter(is_active = True, facebook_account__company = request.user.company).count()
    leads_today = FacebookLead.objects.select_related('facebook_account').filter(
        created_time__gte=timezone.now().date(),
        is_active = True,
        facebook_account__company = request.user.company
    ).count()
    leads_pending = FacebookLead.objects.select_related('facebook_account').filter(processed=False, is_active = True, facebook_account__company = request.user.company).count()
    
    context = {
        'facebook_accounts': accounts,
        'total_accounts': total_accounts,
        'total_leads': total_leads,
        'leads_today': leads_today,
        'leads_pending': leads_pending,
    }
    
    return render(request, 'facebook/facebookDashboard.html', context)


def facebookLeadsList(request):
    """Lista de todos los leads capturados"""
    account_id = request.GET.get('account')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    leads = FacebookLead.objects.select_related('facebook_account').filter(is_active = True , facebook_account__company = request.user.company).order_by('-created_time')
    
    if account_id:
        leads = leads.filter(facebook_account_id=account_id)
    
    if status == 'pending':
        leads = leads.filter(processed=False)
    elif status == 'processed':
        leads = leads.filter(processed=True)
    
    if search:
        leads = leads.filter(raw_payload__icontains=search)
    
    accounts = FacebookAccount.objects.filter(is_active=True, company = request.user.company)
    
    context = {
        'leads': leads,
        'accounts': accounts,
        'selected_account': account_id,
        'selected_status': status,
        'search_query': search,
    }
    
    return render(request, 'facebook/leadsList.html', context)


def facebookLeadDetail(request, lead_id):
    """Ver el detalle completo de un lead"""
    lead = get_object_or_404(FacebookLead, id=lead_id)
    lead_data = []

    if request.method == 'POST':
    
        if lead.raw_payload and 'field_data' in lead.raw_payload:
            for field in lead.raw_payload['field_data']:
                lead_data.append({
                    'name': field.get('name', 'Campo desconocido'),
                    'values': field.get('values', [])
                })
    
    context = {
        'lead': lead,
        'lead_data': lead_data,
    }
    
    return render(request, 'facebook/leadDetail.html', context)


def facebookLeadMarkProcessed(request, lead_id):
    """Marcar un lead como procesado"""
    if request.method == 'POST':
        lead = get_object_or_404(FacebookLead, id=lead_id)
        lead.processed = True
        lead.save()
        messages.success(request, f'✅ Lead marcado como procesado')
    
    return redirect('facebookLeadsList')


def facebookAccountDetail(request, account_id):
    """Ver detalles de una cuenta de Facebook conectada"""
    account = get_object_or_404(FacebookAccount, id=account_id)
    leads = account.leads.order_by('-created_time')[:20]
    
    total_leads = account.leads.count()
    leads_today = account.leads.filter(created_time__gte=timezone.now().date()).count()
    leads_pending = account.leads.filter(processed=False).count()
    
    leads_by_day = []
    for i in range(7):
        day = timezone.now().date() - timedelta(days=i)
        count = account.leads.filter(created_time__date=day).count()
        leads_by_day.append({'date': day, 'count': count})
    leads_by_day.reverse()
    
    context = {
        'account': account,
        'leads': leads,
        'total_leads': total_leads,
        'leads_today': leads_today,
        'leads_pending': leads_pending,
        'leads_by_day': leads_by_day,
    }
    
    return render(request, 'facebook/accountDetail.html', context)




# === MARCAR LEAD COMO PROCESADO ===

def facebookLeadProcess(request, lead_id):
    """Marca un lead como procesado"""
    lead = get_object_or_404(FacebookLead, id=lead_id)
    
    
    lead.processed = True
    lead.save()
    
    messages.success(request, f'Lead #{lead.id} marcado como procesado')
    return redirect('facebookLeadDetail', lead_id=lead.id)



def facebookLeadUnprocess(request, lead_id):
    """Marca un lead como pendiente"""
    lead = get_object_or_404(FacebookLead, id=lead_id)
    
    lead.processed = False
    lead.save()
    
    messages.success(request, f'Lead #{lead.id} marcado como pendiente')
    return redirect('facebookLeadDetail', lead_id=lead.id)


# === ELIMINAR LEAD ===

def facebookLeadDelete(request, lead_id):
    """Elimina un lead"""
    lead = get_object_or_404(FacebookLead, id=lead_id)
    
    # Guardar info para el mensaje
    page_name = lead.facebook_account.page_name
    
    # Marcar como inactivo
    lead.is_active = False
    lead.save(update_fields=["is_active"])
    
    messages.success(request, f'Lead de {page_name} eliminado correctamente')
    return redirect('leadsList')


def facebookAccountDisconnect(request, account_id):
    """Desconecta una cuenta de Facebook"""
    account = get_object_or_404(FacebookAccount, id=account_id)
    
    page_name = account.page_name
    leads_count = account.leads.count()
    
    account.leads.all().delete()  

    
    messages.success(
        request, 
        f'Cuenta "{page_name}" desconectada. {leads_count} leads mantenidos en el sistema'
    )
    
    return redirect('facebook_dashboard')

