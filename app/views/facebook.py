# import json
# import requests
# from django.conf import settings
# from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
# from django.shortcuts import redirect, render
# from django.views.decorators.csrf import csrf_exempt
# from ..models import FacebookAccount, FacebookLead


# def facebook_connect(request):
#     """Redirige al usuario al OAuth de Facebook para conectar su cuenta/página."""
#     client_id = settings.FB_APP_ID
#     redirect_uri = f"{settings.SITE_URL}/facebook/callback/"
#     scope = "pages_show_list,leads_retrieval,pages_manage_metadata"

#     fb_url = (
#         f"https://www.facebook.com/v19.0/dialog/oauth?client_id={client_id}"
#         f"&redirect_uri={redirect_uri}&scope={scope}"
#     )
#     return redirect(fb_url)

# def facebook_callback(request):
#     """Callback de OAuth: intercambia code por token y obtiene la lista de páginas."""
#     code = request.GET.get('code')
#     if not code:
#         return HttpResponseBadRequest('No code provided')

#     token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
#     params = {
#         'client_id': settings.FB_APP_ID,
#         'redirect_uri': f"{settings.SITE_URL}/facebook/callback/",
#         'client_secret': settings.FB_APP_SECRET,
#         'code': code,
#     }
#     r = requests.get(token_url, params=params)
#     data = r.json()
#     user_token = data.get('access_token')
#     if not user_token:
#         return HttpResponseBadRequest('Error obtaining user access token')

#     # Obtener páginas a las que el usuario administra
#     pages_resp = requests.get('https://graph.facebook.com/v19.0/me/accounts', params={'access_token': user_token})
#     pages = pages_resp.json().get('data', [])

#     # Mostrar para que el usuario elija qué página conectar (plantilla simple)
#     return render(request, 'facebook/select_page.html', {'pages': pages, 'user_token': user_token})

# def subscribe_page_to_app(page_id, page_access_token):
#     """Subscribir la app a la página para recibir webhooks (solo leadgen)."""
#     url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"

#     params = {'access_token': page_access_token}
#     data = {
#         'subscribed_fields': 'leadgen'
#     }

#     r = requests.post(url, params=params, data=data)
#     return r.json()

# @csrf_exempt
# def facebook_save_page(request):
#     """Endpoint interno para guardar la página seleccionada desde la plantilla (POST).
#     Este endpoint puede recibir: owner_name, page_id, page_name, page_access_token
#     """
#     if request.method != 'POST':
#         return HttpResponseBadRequest('Method not allowed')

#     payload = request.POST
#     owner_name = payload.get('owner_name') or 'Cliente'
#     page_id = payload.get('page_id')
#     page_name = payload.get('page_name')
#     page_token = payload.get('page_access_token')

#     if not (page_id and page_token):
#         return HttpResponseBadRequest('Missing page_id or page_access_token')

#     # Guardar en BD
#     fb_acc, created = FacebookAccount.objects.update_or_create(
#         page_id=page_id,
#         defaults={
#             'owner_name': owner_name,
#             'page_name': page_name,
#             'page_access_token': page_token,
#             'is_active': True,
#         }
#     )

#     # Suscribir la app a la página (para leadgen):
#     subscribe_resp = subscribe_page_to_app(page_id, page_token)

#     return JsonResponse({'status': 'ok', 'subscribe_resp': subscribe_resp})

# def get_lead_details(leadgen_id, page_access_token):
#     """Llama a la Graph API para recuperar el detalle del lead (field_data)."""
#     url = f"https://graph.facebook.com/v19.0/{leadgen_id}"
#     params = {'access_token': page_access_token}
#     r = requests.get(url, params=params)
#     return r.json()

# @csrf_exempt
# def facebook_webhook(request):
#     """Webhook único para recibir leads de Facebook."""
    
#     # ✅ GET: Verificación inicial de Facebook
#     if request.method == 'GET':
#         mode = request.GET.get('hub.mode')
#         token = request.GET.get('hub.verify_token')
#         challenge = request.GET.get('hub.challenge')
        
#         # Obtener el token de verificación desde settings
#         verify_token = getattr(settings, 'FB_VERIFY_TOKEN', None)
        
#         print(f"🔍 Verificación webhook")
#         print(f"   Mode: {mode}")
#         print(f"   Token recibido: '{token}'")
#         print(f"   Token esperado: '{verify_token}'")
#         print(f"   Challenge: {challenge}")
        
#         # IMPORTANTE: Validar modo y token
#         if mode == 'subscribe' and verify_token and token == verify_token:
#             print("✅ Verificación exitosa - Enviando challenge")
#             return HttpResponse(challenge, content_type='text/plain')
#         else:
#             print(f"❌ Verificación fallida")
#             if not verify_token:
#                 print("   ERROR: FB_VERIFY_TOKEN no está configurado en settings")
#             elif token != verify_token:
#                 print(f"   ERROR: Tokens no coinciden")
#             return HttpResponse('Invalid verify token', status=403)
    
#     # ✅ POST: Recepción de leads
#     elif request.method == 'POST':
#         try:
#             body = json.loads(request.body.decode('utf-8'))
#             print("📩 Webhook recibido:", json.dumps(body, indent=2))
            
#             for entry in body.get('entry', []):
#                 for change in entry.get('changes', []):
#                     if change.get('field') == 'leadgen':
#                         page_id = change['value'].get('page_id')
#                         leadgen_id = change['value'].get('leadgen_id')
                        
#                         print(f"🎯 Lead detectado - Page: {page_id}, Lead ID: {leadgen_id}")
                        
#                         # Buscar la cuenta de Facebook asociada
#                         fb_account = FacebookAccount.objects.filter(page_id=page_id, is_active=True).first()
                        
#                         if fb_account:
#                             # Crear registro del lead
#                             lead = FacebookLead.objects.create(
#                                 facebook_account=fb_account,
#                                 leadgen_id=leadgen_id,
#                                 raw_payload=change['value']
#                             )
                            
#                             # Obtener detalles completos del lead
#                             try:
#                                 detail = get_lead_details(leadgen_id, fb_account.page_access_token)
#                                 lead.raw_payload = detail
#                                 lead.created_time = detail.get('created_time')
#                                 lead.save()
#                                 print(f"✅ Lead {leadgen_id} guardado con detalles")
#                             except Exception as e:
#                                 print(f"⚠️ Error obteniendo detalles del lead: {e}")
#                         else:
#                             print(f"⚠️ No se encontró FacebookAccount para page_id: {page_id}")
            
#             return JsonResponse({'status': 'ok'})
            
#         except Exception as e:
#             print(f"❌ Error procesando webhook: {e}")
#             return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
#     return HttpResponseBadRequest('Método no permitido')

# def facebook_dashboard(request):
#     """Dashboard principal para gestionar conexiones de Facebook"""
#     facebook_accounts = FacebookAccount.objects.filter(is_active=True).order_by('-connected_at')
    
#     return render(request, 'facebook/facebook_dashboard.html', {
#         'facebook_accounts': facebook_accounts
#     })

# import json
# import requests
# from django.conf import settings
# from django.contrib import messages
# from django.db.models import Count, Q
# from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
# from django.shortcuts import redirect, render, get_object_or_404
# from django.utils import timezone
# from django.views.decorators.csrf import csrf_exempt
# from datetime import timedelta
# from ..models import FacebookAccount, FacebookLead


# def facebook_connect(request):
#     """Redirige al usuario al OAuth de Facebook para conectar su cuenta/página."""
#     client_id = settings.FB_APP_ID
#     redirect_uri = f"{settings.SITE_URL}/facebook/callback/"
#     scope = "pages_show_list,leads_retrieval,pages_manage_metadata"

#     fb_url = (
#         f"https://www.facebook.com/v19.0/dialog/oauth?client_id={client_id}"
#         f"&redirect_uri={redirect_uri}&scope={scope}"
#     )
#     return redirect(fb_url)


# def facebook_callback(request):
#     """Callback de OAuth: intercambia code por token y obtiene la lista de páginas."""
#     code = request.GET.get('code')
#     if not code:
#         return HttpResponseBadRequest('No code provided')

#     token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
#     params = {
#         'client_id': settings.FB_APP_ID,
#         'redirect_uri': f"{settings.SITE_URL}/facebook/callback/",
#         'client_secret': settings.FB_APP_SECRET,
#         'code': code,
#     }
#     r = requests.get(token_url, params=params)
#     data = r.json()
#     user_token = data.get('access_token')
#     if not user_token:
#         return HttpResponseBadRequest('Error obtaining user access token')

#     # Obtener páginas a las que el usuario administra
#     pages_resp = requests.get('https://graph.facebook.com/v19.0/me/accounts', params={'access_token': user_token})
#     pages = pages_resp.json().get('data', [])

#     # Mostrar para que el usuario elija qué página conectar (plantilla simple)
#     return render(request, 'facebook/select_page.html', {'pages': pages, 'user_token': user_token})


# def subscribe_page_to_app(page_id, page_access_token):
#     """Subscribir la app a la página para recibir webhooks (solo leadgen)."""
#     url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"
#     params = {'access_token': page_access_token}
#     data = {'subscribed_fields': 'leadgen'}
#     r = requests.post(url, params=params, data=data)
#     return r.json()


# @csrf_exempt
# def facebook_save_page(request):
#     """Endpoint para guardar la página seleccionada y redirigir con mensaje de éxito."""
#     if request.method != 'POST':
#         return HttpResponseBadRequest('Method not allowed')

#     payload = request.POST
#     owner_name = payload.get('owner_name') or 'Cliente'
#     page_id = payload.get('page_id')
#     page_name = payload.get('page_name')
#     page_token = payload.get('page_access_token')

#     if not (page_id and page_token):
#         messages.error(request, 'Error: Faltan datos de la página')
#         return redirect('facebook_dashboard')

#     try:
#         # Guardar en BD
#         fb_acc, created = FacebookAccount.objects.update_or_create(
#             page_id=page_id,
#             defaults={
#                 'owner_name': owner_name,
#                 'page_name': page_name,
#                 'page_access_token': page_token,
#                 'is_active': True,
#             }
#         )

#         # Suscribir la app a la página (para leadgen)
#         subscribe_resp = subscribe_page_to_app(page_id, page_token)
        
#         # Verificar si la suscripción fue exitosa
#         if subscribe_resp.get('success'):
#             if created:
#                 messages.success(request, f'✅ Página "{page_name}" conectada exitosamente. Ya puedes recibir leads automáticamente.')
#             else:
#                 messages.success(request, f'✅ Página "{page_name}" actualizada correctamente.')
#         else:
#             messages.warning(request, f'⚠️ Página guardada pero hubo un problema con la suscripción: {subscribe_resp}')
        
#         return redirect('facebook_dashboard')
        
#     except Exception as e:
#         messages.error(request, f'❌ Error al conectar la página: {str(e)}')
#         return redirect('facebook_dashboard')


# def get_lead_details(leadgen_id, page_access_token):
#     """Llama a la Graph API para recuperar el detalle del lead (field_data)."""
#     url = f"https://graph.facebook.com/v19.0/{leadgen_id}"
#     params = {'access_token': page_access_token}
#     r = requests.get(url, params=params)
#     return r.json()


# @csrf_exempt
# def facebook_webhook(request):
#     """Webhook único para recibir leads de Facebook."""
    
#     # ✅ GET: Verificación inicial de Facebook
#     if request.method == 'GET':
#         mode = request.GET.get('hub.mode')
#         token = request.GET.get('hub.verify_token')
#         challenge = request.GET.get('hub.challenge')
#         verify_token = getattr(settings, 'FB_VERIFY_TOKEN', None)
        
#         print(f"🔍 Verificación webhook")
#         print(f"   Mode: {mode}")
#         print(f"   Token recibido: '{token}'")
#         print(f"   Token esperado: '{verify_token}'")
#         print(f"   Challenge: {challenge}")
        
#         if mode == 'subscribe' and verify_token and token == verify_token:
#             print("✅ Verificación exitosa - Enviando challenge")
#             return HttpResponse(challenge, content_type='text/plain')
#         else:
#             print(f"❌ Verificación fallida")
#             if not verify_token:
#                 print("   ERROR: FB_VERIFY_TOKEN no está configurado en settings")
#             elif token != verify_token:
#                 print(f"   ERROR: Tokens no coinciden")
#             return HttpResponse('Invalid verify token', status=403)
    
#     # ✅ POST: Recepción de leads
#     elif request.method == 'POST':
#         try:
#             body = json.loads(request.body.decode('utf-8'))
#             print("📩 Webhook recibido:", json.dumps(body, indent=2))
            
#             for entry in body.get('entry', []):
#                 for change in entry.get('changes', []):
#                     if change.get('field') == 'leadgen':
#                         page_id = change['value'].get('page_id')
#                         leadgen_id = change['value'].get('leadgen_id')
                        
#                         print(f"🎯 Lead detectado - Page: {page_id}, Lead ID: {leadgen_id}")
                        
#                         fb_account = FacebookAccount.objects.filter(page_id=page_id, is_active=True).first()
                        
#                         if fb_account:
#                             lead = FacebookLead.objects.create(
#                                 facebook_account=fb_account,
#                                 leadgen_id=leadgen_id,
#                                 raw_payload=change['value']
#                             )
                            
#                             try:
#                                 detail = get_lead_details(leadgen_id, fb_account.page_access_token)
#                                 lead.raw_payload = detail
#                                 lead.created_time = detail.get('created_time')
#                                 lead.save()
#                                 print(f"✅ Lead {leadgen_id} guardado con detalles")
#                             except Exception as e:
#                                 print(f"⚠️ Error obteniendo detalles del lead: {e}")
#                         else:
#                             print(f"⚠️ No se encontró FacebookAccount para page_id: {page_id}")
            
#             return JsonResponse({'status': 'ok'})
            
#         except Exception as e:
#             print(f"❌ Error procesando webhook: {e}")
#             return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
#     return HttpResponseBadRequest('Método no permitido')


# def facebook_dashboard(request):
#     """Dashboard principal con resumen de cuentas y leads"""
#     accounts = FacebookAccount.objects.filter(is_active=True).annotate(
#         total_leads=Count('leads'),
#         unprocessed_leads=Count('leads', filter=Q(leads__processed=False))
#     ).order_by('-connected_at')
    
#     total_accounts = accounts.count()
#     total_leads = FacebookLead.objects.count()
#     leads_today = FacebookLead.objects.filter(
#         created_time__gte=timezone.now().date()
#     ).count()
#     leads_pending = FacebookLead.objects.filter(processed=False).count()
    
#     context = {
#         'facebook_accounts': accounts,
#         'total_accounts': total_accounts,
#         'total_leads': total_leads,
#         'leads_today': leads_today,
#         'leads_pending': leads_pending,
#     }
    
#     return render(request, 'facebook/facebook_dashboard.html', context)


# def facebook_leads_list(request):
#     """Lista de todos los leads capturados"""
#     account_id = request.GET.get('account')
#     status = request.GET.get('status')
#     search = request.GET.get('search')
    
#     leads = FacebookLead.objects.select_related('facebook_account').order_by('-created_time')
    
#     if account_id:
#         leads = leads.filter(facebook_account_id=account_id)
    
#     if status == 'pending':
#         leads = leads.filter(processed=False)
#     elif status == 'processed':
#         leads = leads.filter(processed=True)
    
#     if search:
#         leads = leads.filter(raw_payload__icontains=search)
    
#     accounts = FacebookAccount.objects.filter(is_active=True)
    
#     context = {
#         'leads': leads,
#         'accounts': accounts,
#         'selected_account': account_id,
#         'selected_status': status,
#         'search_query': search,
#     }
    
#     return render(request, 'facebook/leads_list.html', context)


# def facebook_lead_detail(request, lead_id):
#     """Ver el detalle completo de un lead"""
#     lead = get_object_or_404(FacebookLead, id=lead_id)
    
#     lead_data = []
#     if lead.raw_payload and 'field_data' in lead.raw_payload:
#         for field in lead.raw_payload['field_data']:
#             lead_data.append({
#                 'name': field.get('name', 'Campo desconocido'),
#                 'values': field.get('values', [])
#             })
    
#     context = {
#         'lead': lead,
#         'lead_data': lead_data,
#     }
    
#     return render(request, 'facebook/lead_detail.html', context)


# def facebook_lead_mark_processed(request, lead_id):
#     """Marcar un lead como procesado"""
#     if request.method == 'POST':
#         lead = get_object_or_404(FacebookLead, id=lead_id)
#         lead.processed = True
#         lead.save()
#         messages.success(request, f'✅ Lead marcado como procesado')
    
#     return redirect('facebook_leads_list')


# def facebook_account_detail(request, account_id):
#     """Ver detalles de una cuenta de Facebook conectada"""
#     account = get_object_or_404(FacebookAccount, id=account_id)
#     leads = account.leads.order_by('-created_time')[:20]
    
#     total_leads = account.leads.count()
#     leads_today = account.leads.filter(created_time__gte=timezone.now().date()).count()
#     leads_pending = account.leads.filter(processed=False).count()
    
#     leads_by_day = []
#     for i in range(7):
#         day = timezone.now().date() - timedelta(days=i)
#         count = account.leads.filter(created_time__date=day).count()
#         leads_by_day.append({'date': day, 'count': count})
#     leads_by_day.reverse()
    
#     context = {
#         'account': account,
#         'leads': leads,
#         'total_leads': total_leads,
#         'leads_today': leads_today,
#         'leads_pending': leads_pending,
#         'leads_by_day': leads_by_day,
#     }
    
#     return render(request, 'facebook/account_detail.html', context)


# def facebook_account_disconnect(request, account_id):
#     """Desconectar una cuenta de Facebook"""
#     if request.method == 'POST':
#         account = get_object_or_404(FacebookAccount, id=account_id)
#         account.is_active = False
#         account.save()
#         messages.success(request, f'✅ Cuenta "{account.page_name}" desconectada exitosamente')
#         return redirect('facebook_dashboard')
    
#     return redirect('facebook_dashboard')


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


def facebook_connect(request):
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


def facebook_callback(request):
    """Callback de OAuth: intercambia code por token y obtiene la lista de páginas."""
    code = request.GET.get('code')
    if not code:
        return HttpResponseBadRequest('No code provided')

    token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
    params = {
        'client_id': settings.FB_APP_ID,
        'redirect_uri': f"{settings.SITE_URL}/facebook/callback/",
        'client_secret': settings.FB_APP_SECRET,
        'code': code,
    }
    r = requests.get(token_url, params=params)
    data = r.json()
    short_token = data.get('access_token')
    if not short_token:
        return HttpResponseBadRequest('Error obtaining user access token')

    # Intercambiar por un token de larga duración
    long_token_url = 'https://graph.facebook.com/v19.0/oauth/access_token'
    long_params = {
        'grant_type': 'fb_exchange_token',
        'client_id': settings.FB_APP_ID,
        'client_secret': settings.FB_APP_SECRET,
        'fb_exchange_token': short_token
    }
    long_r = requests.get(long_token_url, params=long_params)
    long_data = long_r.json()
    user_token = long_data.get('access_token', short_token)

    # Obtener páginas a las que el usuario administra
    pages_resp = requests.get('https://graph.facebook.com/v19.0/me/accounts', params={'access_token': user_token})
    pages = pages_resp.json().get('data', [])

    # Mostrar para que el usuario elija qué página conectar (plantilla simple)
    return render(request, 'facebook/select_page.html', {'pages': pages, 'user_token': user_token})


def subscribe_page_to_app(page_id, page_access_token):
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
def facebook_save_page(request):
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
        return redirect('facebook_dashboard')

    try:
        # Guardar en BD
        fb_acc, created = FacebookAccount.objects.update_or_create(
            page_id=page_id,
            defaults={
                'owner_name': owner_name,
                'page_name': page_name,
                'page_access_token': page_token,
                'is_active': True,
            }
        )

        # Suscribir la app a la página (para leadgen)
        subscribe_resp = subscribe_page_to_app(page_id, page_token)
        
        # Verificar si la suscripción fue exitosa
        if subscribe_resp.get('success'):
            if created:
                messages.success(request, f'✅ Página "{page_name}" conectada exitosamente. Ya puedes recibir leads automáticamente.')
            else:
                messages.success(request, f'✅ Página "{page_name}" actualizada correctamente.')
        else:
            messages.warning(request, f'⚠️ Página guardada pero hubo un problema con la suscripción: {subscribe_resp}')
        
        return redirect('facebook_dashboard')
        
    except Exception as e:
        messages.error(request, f'❌ Error al conectar la página: {str(e)}')
        return redirect('facebook_dashboard')


def get_lead_details(leadgen_id, page_access_token):
    """Llama a la Graph API para recuperar el detalle del lead (field_data)."""
    url = f"https://graph.facebook.com/v19.0/{leadgen_id}"
    params = {'access_token': page_access_token}
    r = requests.get(url, params=params)
    return r.json()


@csrf_exempt
def facebook_webhook(request):
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
                                raw_payload=change['value']
                            )
                            
                            try:
                                detail = get_lead_details(leadgen_id, fb_account.page_access_token)
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


def facebook_dashboard(request):
    """Dashboard principal con resumen de cuentas y leads"""
    accounts = FacebookAccount.objects.filter(is_active=True).annotate(
        total_leads=Count('leads'),
        unprocessed_leads=Count('leads', filter=Q(leads__processed=False))
    ).order_by('-connected_at')
    
    total_accounts = accounts.count()
    total_leads = FacebookLead.objects.count()
    leads_today = FacebookLead.objects.filter(
        created_time__gte=timezone.now().date()
    ).count()
    leads_pending = FacebookLead.objects.filter(processed=False).count()
    
    context = {
        'facebook_accounts': accounts,
        'total_accounts': total_accounts,
        'total_leads': total_leads,
        'leads_today': leads_today,
        'leads_pending': leads_pending,
    }
    
    return render(request, 'facebook/facebook_dashboard.html', context)


def facebook_leads_list(request):
    """Lista de todos los leads capturados"""
    account_id = request.GET.get('account')
    status = request.GET.get('status')
    search = request.GET.get('search')
    
    leads = FacebookLead.objects.select_related('facebook_account').order_by('-created_time')
    
    if account_id:
        leads = leads.filter(facebook_account_id=account_id)
    
    if status == 'pending':
        leads = leads.filter(processed=False)
    elif status == 'processed':
        leads = leads.filter(processed=True)
    
    if search:
        leads = leads.filter(raw_payload__icontains=search)
    
    accounts = FacebookAccount.objects.filter(is_active=True)
    
    context = {
        'leads': leads,
        'accounts': accounts,
        'selected_account': account_id,
        'selected_status': status,
        'search_query': search,
    }
    
    return render(request, 'facebook/leads_list.html', context)


def facebook_lead_detail(request, lead_id):
    """Ver el detalle completo de un lead"""
    lead = get_object_or_404(FacebookLead, id=lead_id)
    
    lead_data = []
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
    
    return render(request, 'facebook/lead_detail.html', context)


def facebook_lead_mark_processed(request, lead_id):
    """Marcar un lead como procesado"""
    if request.method == 'POST':
        lead = get_object_or_404(FacebookLead, id=lead_id)
        lead.processed = True
        lead.save()
        messages.success(request, f'✅ Lead marcado como procesado')
    
    return redirect('facebook_leads_list')


def facebook_account_detail(request, account_id):
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
    
    return render(request, 'facebook/account_detail.html', context)


def facebook_account_disconnect(request, account_id):
    """Desconectar una cuenta de Facebook"""
    if request.method == 'POST':
        account = get_object_or_404(FacebookAccount, id=account_id)
        account.is_active = False
        account.save()
        messages.success(request, f'✅ Cuenta "{account.page_name}" desconectada exitosamente')
        return redirect('facebook_dashboard')
    
    return redirect('facebook_dashboard')

