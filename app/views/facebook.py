import json
import requests
from django.conf import settings
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from ..models import FacebookAccount, FacebookLead


def facebook_connect(request):
    """Redirige al usuario al OAuth de Facebook para conectar su cuenta/página."""
    client_id = settings.FB_APP_ID
    redirect_uri = f"{settings.SITE_URL}/facebook/callback/"
    scope = "pages_show_list,leads_retrieval,pages_manage_metadata"

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
    user_token = data.get('access_token')
    if not user_token:
        return HttpResponseBadRequest('Error obtaining user access token')

    # Obtener páginas a las que el usuario administra
    pages_resp = requests.get('https://graph.facebook.com/v19.0/me/accounts', params={'access_token': user_token})
    pages = pages_resp.json().get('data', [])

    # Mostrar para que el usuario elija qué página conectar (plantilla simple)
    return render(request, 'facebook/select_page.html', {'pages': pages, 'user_token': user_token})

def subscribe_page_to_app(page_id, page_access_token):
    """Subscribir la app a la página para recibir webhooks (solo leadgen)."""
    url = f"https://graph.facebook.com/v19.0/{page_id}/subscribed_apps"

    params = {'access_token': page_access_token}
    data = {
        'subscribed_fields': 'leadgen'
    }

    r = requests.post(url, params=params, data=data)
    return r.json()

@csrf_exempt
def facebook_save_page(request):
    """Endpoint interno para guardar la página seleccionada desde la plantilla (POST).
    Este endpoint puede recibir: owner_name, page_id, page_name, page_access_token
    """
    if request.method != 'POST':
        return HttpResponseBadRequest('Method not allowed')

    payload = request.POST
    owner_name = payload.get('owner_name') or 'Cliente'
    page_id = payload.get('page_id')
    page_name = payload.get('page_name')
    page_token = payload.get('page_access_token')

    if not (page_id and page_token):
        return HttpResponseBadRequest('Missing page_id or page_access_token')

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

    # Suscribir la app a la página (para leadgen):
    subscribe_resp = subscribe_page_to_app(page_id, page_token)

    return JsonResponse({'status': 'ok', 'subscribe_resp': subscribe_resp})

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
        
        # Obtener el token de verificación desde settings
        verify_token = getattr(settings, 'FB_VERIFY_TOKEN', None)
        
        print(f"🔍 Verificación webhook")
        print(f"   Mode: {mode}")
        print(f"   Token recibido: '{token}'")
        print(f"   Token esperado: '{verify_token}'")
        print(f"   Challenge: {challenge}")
        
        # IMPORTANTE: Validar modo y token
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
                        
                        # Buscar la cuenta de Facebook asociada
                        fb_account = FacebookAccount.objects.filter(page_id=page_id, is_active=True).first()
                        
                        if fb_account:
                            # Crear registro del lead
                            lead = FacebookLead.objects.create(
                                facebook_account=fb_account,
                                leadgen_id=leadgen_id,
                                raw_payload=change['value']
                            )
                            
                            # Obtener detalles completos del lead
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
    """Dashboard principal para gestionar conexiones de Facebook"""
    facebook_accounts = FacebookAccount.objects.filter(is_active=True).order_by('-connected_at')
    
    return render(request, 'facebook/facebook_dashboard.html', {
        'facebook_accounts': facebook_accounts
    })




