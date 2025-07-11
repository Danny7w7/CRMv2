import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from ..models import Leads, LeadExtraField

@csrf_exempt
def obtainLeadsByGoHighLevel(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))
        print(data)
        
        full_name = data.pop('full_name', '')
        first_name, last_name = split_full_name(full_name)
        print(f'{first_name} - {last_name}')

        # Campos esperados del modelo Leads
        expected_fields = {'first_name', 'last_name', 'full_name','phone', 'email', 'full_address', 'city', 'state', 'postal_code'}

        # Crear el lead principal
        lead = Leads.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=int(data.get('phone', 0)),
            email=data.get('email'),
            address=data.get('full_address'),
            city=data.get('city'),
            state=data.get('state'),
            zipCode=int(data.get('postal_code', 0)) if data.get('postal_code') else None
        )

        # Guardar campos extra
        for key, value in data.items():
            if key not in expected_fields and key != 'first_name':
                LeadExtraField.objects.create(
                    lead=lead,
                    field_name=key,
                    field_value=value
                )

        return JsonResponse({'status': 'success'})


def split_full_name(full_name):
    parts = full_name.strip().split()

    if len(parts) == 0:
        return '', ''
    elif len(parts) == 1:
        return parts[0], ''
    elif len(parts) == 2:
        return parts[0], parts[1]
    else:
        first_name = ' '.join(parts[:-2])
        last_name = ' '.join(parts[-2:])
        return first_name, last_name