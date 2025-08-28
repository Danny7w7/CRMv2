from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import pandas as pd
from app.modelsDialer import *
import re
from django.db.models import Count, Q


@login_required(login_url='/login') 
def campaigns(request):
    return render(request, 'dialer/adminDashboard.html')

def getListCampaigns(request):
    if request.method == 'GET':
        campaigns = Campaign.objects.annotate(
            total_contacts=Count('contacts', distinct=True),
            marked_contacts=Count(
                'contacts',
                filter=Q(contacts__calls__outcome__isnull=False),
                distinct=True
            ),
            calling_contacts=Count(
                'contacts',
                filter=Q(contacts__calls__status='connected_to_agent'),
                distinct=True
            )
        )
        
        campaigns_data = []
        for campaign in campaigns:
            # Status de la campaña
            if not campaign.is_active:
                status = "paused"
            elif campaign.total_contacts == 0:
                status = "draft"
            elif campaign.marked_contacts == campaign.total_contacts and campaign.total_contacts > 0:
                status = "completed"
            else:
                status = "active"
            
            campaigns_data.append({
                'id': campaign.id,
                'name': campaign.name,
                'description': campaign.description or "",
                'totalContacts': campaign.total_contacts,
                'markedContacts': campaign.marked_contacts,
                'status': status,
                'createdDate': campaign.created_at.strftime('%Y-%m-%d'),
                'isMarking': campaign.calling_contacts > 0
            })
        
        return JsonResponse(campaigns_data, safe=False)
    return HttpResponseBadRequest('Invalid request')


def createCampaigns(request):
    if request.method == 'POST':
        Campaign.objects.create(
            name = request.POST.get('name'),
            description = request.POST.get('description')
        )
        return JsonResponse({'message': 'Campaign created successfully'})
    return HttpResponseBadRequest('Invalid request')

def processExcelForDialer(request):
    if request.method == 'POST':
        campaign = Campaign.objects.get(id=request.POST.get('campaignId'))
        file = request.FILES.get('inputFile')
        
        # Detect file extension
        extension = file.name.split('.')[-1].lower()

        if extension in ['xlsx', 'xls']:
            dataFrame = pd.read_excel(file)
        elif extension == 'csv':
            dataFrame = pd.read_csv(file)

        rowsErrors = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
        rowsSuccess = pd.DataFrame(columns=dataFrame.columns)

        for index, row in dataFrame.iterrows():
            nameCol = request.POST.get('name')
            phoneCol = request.POST.get('phoneNumber')
            addressCol = request.POST.get('address')

            name = row[nameCol] if nameCol in row and not pd.isna(row[nameCol]) else ''
            phoneNumber = row[phoneCol] if phoneCol in row and not pd.isna(row[phoneCol]) else ''
            address = row[addressCol] if addressCol in row and not pd.isna(row[addressCol]) else ''

            try:
                formatedPhoneNumber = parsePhoneNumber(phoneNumber)
                lead = LeadsDialer.objects.create(
                    campaign=campaign,
                    name=name,
                    phone_number=formatedPhoneNumber,
                    address=address
                )
                rowsSuccess.loc[len(rowsSuccess)] = row
            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                rowsErrors.loc[len(rowsErrors)] = rowWithError

    return JsonResponse({
        'success':rowsSuccess.to_dict(orient='records'),
        'errors':rowsErrors.to_dict(orient='records')
    })

def parsePhoneNumber(phoneNumber: str) -> int:
    # Ensure input is string
    phoneNumber = str(phoneNumber)

    # Remove everything except digits
    digits = re.sub(r'\D', '', phoneNumber)
    
    # If the number starts without a country code, assume '1' (USA)
    if len(digits) == 10:
        digits = '1' + digits
    
    # Validate that the result looks like a valid E.164 number
    if not (10 < len(digits) <= 15):
        raise ValueError(f"Invalid phone number format: {phoneNumber}")
    
    return int(digits)