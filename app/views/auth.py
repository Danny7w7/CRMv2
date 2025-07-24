# Standard Python libraries
import random
import datetime
import requests

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

    todos_los_planes = [] # Esta lista acumulará todos los planes
    year = datetime.datetime.now().year

    if request.method == 'POST':
        try:
            ingreso = float(request.POST.get('ingreso'))
            estado = request.POST.get('estado', '').strip().upper()
            zipcode = request.POST.get('zipcode')
            countyfips = obtenerCountyfips(zipcode)

            if not estado or len(estado) != 2:
                raise ValueError("Estado inválido o vacío")
            if not countyfips or len(str(countyfips)) != 5:
                raise ValueError("FIPS inválido o no encontrado")

            people = []
            index = 0
            while f"edad_{index}" in request.POST:
                edad = int(request.POST.get(f"edad_{index}"))
                genero = request.POST.get(f"genero_{index}")
                tabaco = request.POST.get(f"tabaco_{index}") == 'on'

                persona = {
                    "age": edad,
                    "aptc_eligible": True,
                    "gender": genero,
                    "uses_tobacco": tabaco
                }
                people.append(persona)
                index += 1

            if not people:
                raise ValueError("No se agregó ninguna persona al hogar")

            API_KEY = settings.CMS_SECRET_KEY
            url = f"https://marketplace.api.healthcare.gov/api/v1/plans/search?apikey={API_KEY}"

            # *** Lógica de paginación ***
            offset = 0
            total_planes_disponibles = -1 # Inicializar para entrar en el bucle

            # Bucle para obtener todas las páginas de resultados
            while total_planes_disponibles == -1 or offset < total_planes_disponibles:
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

                if response.status_code == 200:

                    data = response.json()
                    # Si no hay planes en esta respuesta, o si el atributo 'results' no existe, salir del bucle
                    if not data.get('plans'):
                        break

                    # Acumular los planes de la página actual
                    todos_los_planes.extend(data['plans'])

                    # Actualizar el total de planes disponibles (solo una vez o si cambia)
                    if total_planes_disponibles == -1:
                        total_planes_disponibles = data.get('total', 0) # Obtener el total de planes disponibles

                    # Incrementar el offset para la siguiente página
                    offset += len(data['plans']) # Incrementa por la cantidad de planes recibidos (debería ser 10)

                    # Si la cantidad de planes en la respuesta es menor que el límite de página
                    # (que sabemos es 10), significa que ya llegamos al final.
                    if len(data['plans']) < 10:
                        break 

                elif response.status_code == 429:                    
                    # Por simplicidad pero aqui debe ir la logica de esperar antes de reintentar, por ahora solo agregamos un mensaje de error y salimos.
                    todos_los_planes = {"error": f"Límite de tasa excedido. Por favor, espera y reintenta. {response.text}"}
                    break
                else:
                    # Manejo de otros errores de la API
                    todos_los_planes = {"error": f"Error {response.status_code} de la API: {response.text}"}
                    break 

            # Después del bucle, asigna la lista acumulada a 'planes'
            planes = todos_los_planes

        except Exception as e:
            planes = {"error": f"Error en los datos enviados o procesamiento: {str(e)}"}

    return render(request, "forms/formQuotation.html", {
        "planes": planes,
        "post_data": request.POST if request.method == 'POST' else {}
    })

