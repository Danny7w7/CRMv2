# Standard Python libraries
import random
import datetime
import requests
import pprint

# Django utilities
from django.http import JsonResponse
from django.conf import settings

# Django core libraries
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render 

# Application-specific imports
from app.models import *
from .index import index

def login_(request):
    if request.user.is_authenticated:
        return redirect(index)
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        companyUser = Users.objects.filter(username=username).first()
        company = companyUser and Companies.objects.filter(id=companyUser.company.id, is_active=True).exists() or None

        user = authenticate(request, username=username, password=password)
        if user and company is not None:
            login(request, user)
            return redirect(motivationalPhrase)
        else:
            msg = 'Datos incorrectos, intente de nuevo'
            return render(request, 'auth/login.html', {'msg':msg})
    else:
        return render(request, 'auth/login.html')
        
def logout_(request):
    # Verifica si es una solicitud AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        logout(request)
        return JsonResponse({
            'status': 'success', 
            'redirect_url': '/login/'  # URL a la que redirigir después del logout
        })
    else:
        # Cierre de sesión manual tradicional
        logout(request)
        return redirect(login_)
    
@login_required(login_url='/login')
def motivationalPhrase(request):
    randomInt = random.randint(1,174)
    motivation = Motivation.objects.filter(id=randomInt).first()
    user = Users.objects.select_related('company').filter(id = request.user.id).first()
    context = {
        'motivation':motivation,
        'user':user
        }
    return render (request, 'auth/motivationalPhrase.html',context)

def obtenerLatLon(zipcode):
    try:
        response = requests.get(f"http://api.zippopotam.us/us/{zipcode}")
        if response.status_code == 200:
            data = response.json()
            place = data['places'][0]
            return place['latitude'], place['longitude']
    except:
        pass
    return None, None

def obtenerCountyfips(zipcode):
    lat, lon = obtenerLatLon(zipcode)
    if lat and lon:
        try:
            url = f"https://geo.fcc.gov/api/census/block/find?format=json&latitude={lat}&longitude={lon}"
            response = requests.get(url)
            data = response.json()
            return data.get("County", {}).get("FIPS")
        except:
            pass
    return None

def buscarPlanes(request):

    planes = []
    post_data = {}
    year = datetime.datetime.now().year # Se define el año al inicio

    if request.method == 'POST':
        try:
            # Captura los datos del POST. Usamos .copy() para hacerla mutable si es necesario.
            post_data = request.POST.copy()

            # --- Recolección y Validación de Datos del Formulario ---
            ingreso = float(request.POST.get('ingreso'))
            estado = request.POST.get('estado', '').strip().upper()
            zipcode = request.POST.get('zipcode')
            
            # Obtener FIPS usando tu función existente
            countyfips = obtenerCountyfips(zipcode) 

            # Validaciones básicas
            if not estado or len(estado) != 2:
                raise ValueError("Estado inválido o vacío. Debe ser un código de 2 letras (ej. FL, CA).")
            if not countyfips:
                raise ValueError("Código postal inválido o FIPS no encontrado para el código postal y estado dados.")

            # Recolectar datos de las personas (aplicante principal + dependientes)
            people = []
            index = 0
            while f"edad_{index}" in request.POST:
                try:
                    edad = int(request.POST.get(f"edad_{index}"))
                    genero = request.POST.get(f"genero_{index}")
                    tabaco = request.POST.get(f"tabaco_{index}") == 'on' # Convertir a booleano

                    # Validaciones para cada persona
                    if not (0 <= edad <= 100):
                        raise ValueError(f"Edad inválida para persona #{index}: {edad}. Debe ser entre 0 y 100.")
                    if genero not in ['Female', 'Male']:
                        raise ValueError(f"Género inválido para persona #{index}: '{genero}'. Debe ser 'Female' o 'Male'.")

                    persona = {
                        "age": edad,
                        "aptc_eligible": True, # Asumiendo elegibilidad por defecto
                        "gender": genero,
                        "uses_tobacco": tabaco
                    }
                    people.append(persona)
                except ValueError as ve:
                    # Captura errores de conversión o validación de datos de la persona
                    raise ValueError(f"Error en los datos de la persona #{index}: {ve}")
                index += 1

            if not people:
                raise ValueError("Debe agregar al menos una persona al hogar.")

            # --- Configuración y Llamada a la API de Healthcare.gov ---
            API_KEY = settings.CMS_SECRET_KEY
            url = f"https://marketplace.api.healthcare.gov/api/v1/plans/search?apikey={API_KEY}"

            todos_los_planes = [] # Lista para acumular todos los planes de la paginación
            offset = 0
            total_planes_disponibles = -1 # Se actualizará con el total real de la API
            
            MAX_PLANS_TO_FETCH = 50 # <-- LÍMITE DE PLANES A OBTENER

            # Bucle para obtener planes en páginas hasta alcanzar el límite o el final de la API
            while True: # Bucle infinito que se romperá con las condiciones internas
                # Detener si ya hemos recopilado suficientes planes
                if len(todos_los_planes) >= MAX_PLANS_TO_FETCH:
                    break

                payload = {
                    "household": {
                        "income": ingreso,
                        "people": people
                    },
                    "market": "Individual",
                    "place": {
                        "state": estado,
                        "zipcode": zipcode,
                        "countyfips": countyfips
                    },
                    "year": year,
                    "offset": offset 
                }

                headers = {
                    "Content-Type": "application/json"
                }

                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status() # Lanza HTTPError para códigos de estado 4xx/5xx

                data = response.json()
                
                # Si la API no devuelve la clave 'plans' o si está vacía, detener
                current_page_plans = data.get('plans')
                if not current_page_plans:
                    break 

                # Acumular planes de la página actual, respetando el límite
                for plan in current_page_plans:
                    if len(todos_los_planes) < MAX_PLANS_TO_FETCH:
                        todos_los_planes.append(plan)
                    else:
                        break # Si ya alcanzamos el límite, no añadimos más de esta página

                # Actualizar el total de planes disponibles reportado por la API (solo una vez)
                if total_planes_disponibles == -1:
                    total_planes_disponibles = data.get('total', 0)

                # Incrementar el offset para la siguiente solicitud
                offset += len(current_page_plans)
                
                # Si la cantidad de planes en la respuesta actual es menor que el tamaño de página esperado (10),
                # significa que es la última página de resultados de la API.
                if len(current_page_plans) < 10: # Asumiendo un tamaño de página de 10 por la API
                    break
                
                # Si el offset ya ha alcanzado o superado el total de planes disponibles reportados
                if offset >= total_planes_disponibles and total_planes_disponibles != 0:
                    break # Se han obtenido todos los planes que la API dijo tener

            # Si todo el proceso de búsqueda fue exitoso, asigna los planes acumulados (truncados al límite)
            planes = todos_los_planes[:MAX_PLANS_TO_FETCH]

        # --- Manejo de Excepciones ---
        except requests.exceptions.HTTPError as e:
            # Errores HTTP de la API (ej. 404, 500)
            planes = {"error": f"Error de la API ({e.response.status_code}): {e.response.text}"}
        except requests.exceptions.RequestException as e:
            # Errores de conexión de red (DNS, timeout)
            planes = {"error": f"Error de conexión al servidor de planes: {e}"}
        except ValueError as e:
            # Errores de validación de datos del formulario o de conversión (float, int)
            planes = {"error": f"Error en los datos del formulario: {str(e)}"}
        except Exception as e:
            # Cualquier otra excepción inesperada
            planes = {"error": f"Error inesperado al procesar la solicitud: {str(e)}"}

    return render(request, "forms/formQuotation.html", {
        "planes": planes,
        "post_data": post_data
    })

