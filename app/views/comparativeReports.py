# Standard Python libraries
from datetime import datetime, date
import pandas as pd
import numpy as np
import re

# Django utilities
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

# Django core libraries

# Third-party imports

# Application-specific imports
from app.models import *
from app.modelsSMS import *

def uploadReports(request):
    return render(request, 'comparative/uploadReports.html')

def processExcel(request):
    if request.method == 'POST':
        uploadedFile = request.FILES['file']
        try:
            # Detect file extension
            fileExtension = uploadedFile.name.split('.')[-1].lower()
            
            if fileExtension in ['xlsx', 'xls']:
                dataFrame = pd.read_excel(uploadedFile)
            elif fileExtension == 'csv':
                dataFrame = pd.read_csv(uploadedFile)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al procesar el archivo: {str(e)}'
            })

        if request.POST.get('reportingTypeFinally') == 'oneil':
            matchedRecords, unmatchedRecords = getDetailReportOneil(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'sherpa':
            matchedRecords, unmatchedRecords = getDetailReportSherpa(request, dataFrame)

        elif request.POST.get('reportingTypeFinally') == 'aetna':
            matchedRecords, unmatchedRecords = getDetailReportAetna(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'ambetter':
            matchedRecords, unmatchedRecords = getDetailReportAmbetter(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'amerihealth':
            matchedRecords, unmatchedRecords = getDetailReportAmeriHealth(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'anthem':
            matchedRecords, unmatchedRecords = getDetailReportAnthem(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'bluecross':
            matchedRecords, unmatchedRecords = getDetailReportBluecross(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'bluecrossaz':
            matchedRecords, unmatchedRecords = getDetailReportBluecrossArizona(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'caresource':
            matchedRecords, unmatchedRecords = getDetailReportCaresource(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'cigna':
            matchedRecords, unmatchedRecords = getDetailReportCigna(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'medica':
            matchedRecords, unmatchedRecords = getDetailReportMedica(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'molina':
            matchedRecords, unmatchedRecords = getDetailReportMolina(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'oscar':
            matchedRecords, unmatchedRecords = getDetailReportOscar(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'united':
            matchedRecords, unmatchedRecords = getDetailReportUnited(request, dataFrame)

        elif request.POST.get('reportingTypeFinally') == 'suppStatusMetlife':
            matchedRecords, unmatchedRecords = getDetailReportSuppStatusMetlife(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'suppStatusCigna':
            matchedRecords, unmatchedRecords = getDetailReportSuppStatusCigna(request, dataFrame)
        elif request.POST.get('reportingTypeFinally') == 'suppStatusUnited':
            matchedRecords, unmatchedRecords = getDetailReportSuppStatusUnited(request, dataFrame)

        elif request.POST.get('reportingTypeFinally') == 'suppPaymentsCigna':
            matchedRecords, unmatchedRecords = getDetailReportSuppPaymentsCigna(request, dataFrame)

        return JsonResponse({
            'status': 'success',
            'modalId': 'oneil',
            'matchedRecords': cleanForJson(matchedRecords),
            'unmatchedRecords': cleanForJson(unmatchedRecords)
        })

def getDetailReportAetna(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Aetna',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportAmbetter(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        eligibleForCommission = row[request.POST.get('eligibleForCommission')]
        policyEffectiveDate = row[request.POST.get('policyEffectiveDate')]
        
        if parseDateMDY(policyEffectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila

                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Ambetter',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if eligibleForCommission == 'Yes' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportAmeriHealth(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=str(policyNumber)[:-2])
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=str(policyNumber)[:-2])
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila

                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='AmeriHealth',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportAnthem(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if effectiveDate.date() > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Anthem',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportBluecross(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)
    
    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila

                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Bluecross',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportBluecrossArizona(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        effectiveDate = row[request.POST.get('effectiveDate')]
        policyStatus = request.POST.get('policyStatus')

        if parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=f'000{policyNumber}')
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=f'000{policyNumber}')
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Bluecross',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportCaresource(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Caresource',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportCigna(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Cigna',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportMedica(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Identificar pólizas duplicadas
    duplicatedPolicies = dataFrame.copy()
    
    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        # Obtener todos los registros para esta póliza
        duplicateRows = duplicatedPolicies[duplicatedPolicies[request.POST.get('policyNumber')] == policyNumber]
        # Convertir las fechas efectivas y obtener la última
        duplicateRows['effectiveDate_parsed'] = duplicateRows[request.POST.get('effectiveDate')].apply(parseDateMDY)
        latestRow = duplicateRows.loc[duplicateRows['effectiveDate_parsed'].idxmax()]

        # Si es la fila más reciente, procesarla
        if policyNumber == latestRow['Member ID'] and parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Medica',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportMolina(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        hixId = row[request.POST.get('hixId')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if policyNumber == hixId and parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Molina',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportOscar(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if parseDateMDY(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='Oscar',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportUnited(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    policyStatus = request.POST.get('policyStatus')
    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        effectiveDate = row[request.POST.get('effectiveDate')]

        if parseDateYMD(effectiveDate) > date(2024, 12, 31):
            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber__startswith=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber__startswith=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila
                
                PaymentsCarriers.objects.create(
                    obamacare=obamacare,
                    carrier='United',
                    created_at=datetime.now(),
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportOneil(request, dataFrame):
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        coverageMonth = row[request.POST.get('coverageMonth')]
        carrierName = row[request.POST.get('carrierName')]
        agency = row[request.POST.get('agency')]
        payable = row[request.POST.get('payable')]
        statementDate = row[request.POST.get('statementDate')]

        if carrierName == 'AmeriHealth Caritas':
            policyNumber = policyNumber.split('-')[0]

        try:
            obamacare = None

            # Intentar obtener ObamaCare
            try:
                obamacare = ObamaCare.objects.get(policyNumber=policyNumber)
            except ObamaCare.DoesNotExist:
                # Si no existe ObamaCare, intentar con Dependent
                try:
                    dependent = Dependents.objects.get(policyNumber=policyNumber)
                    obamacare = dependent.obamacare
                except Dependents.DoesNotExist:
                    rowWithError = pd.Series(row)
                    rowWithError['Error Reason'] = 'No ObamaCare policy found for holder or dependent.'
                    unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError
                    continue  # saltar a la siguiente fila

            # Crear el pago si se obtuvo obamacare
            PaymentsOneil.objects.create(
                obamacare=obamacare,
                agency=agency,
                coverageMonth=parseMonthYear(coverageMonth),
                created_at=datetime.now(),
                payday=parseDateMDY(statementDate),
                payable=payable
            )
            matchedRecords.loc[len(matchedRecords)] = row

        except ObamaCare.MultipleObjectsReturned:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = 'Multiple ObamaCare found'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

        except Exception as e:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = f'Error: {str(e)}'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords


def getDetailReportSherpa(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        carrier = row[request.POST.get('carrier')]
        state = row[request.POST.get('state')]
        policyNumber = row[request.POST.get('policyNumber')]
        subscriberId = row[request.POST.get('subscriberId')]
        ffm = row[request.POST.get('ffm')]
        effectiveDate = row[request.POST.get('effectiveDate')]
        policyStatus = row[request.POST.get('policyStatus')]
        
        carrierLower = carrier.lower()

        if parseDateMDY(effectiveDate) > date(2024, 12, 31):
            try:
                formattedPolicyNumber = formatPolicyNumberByCarrier(policyNumber, subscriberId, carrier, state)
                if 'cigna' in carrierLower:
                    obamacare = ObamaCare.objects.get(ffm=ffm)
                else:
                    obamacare = ObamaCare.objects.get(policyNumber__contains=formattedPolicyNumber)
                PaymentsSherpa.objects.create(
                    obamacare=obamacare,
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Effectuated' else False
                )
                # Agregar el registro asociado al DataFrame
                matchedRecords.loc[len(matchedRecords)] = row

            except ValueError as ve:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = str(ve)
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except ObamaCare.DoesNotExist:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Obamacare not found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except ObamaCare.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple ObamaCare found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportSuppStatusMetlife(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]
        policyType = row[request.POST.get('policyType')]

        try:
            policyType = classifyLabel(policyType)
            supp = Supp.objects.get(policyNumber=policyNumber, policy_type=policyType)
            PaymentsSuplementals.objects.create(
                supp=supp,
                coverageMonth=datetime.now(),
                is_active=True if policyStatus == 'Approved' else False
            )
            # Agregar el registro asociado al DataFrame
            matchedRecords.loc[len(matchedRecords)] = row

        except Supp.DoesNotExist:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = 'Suplemental not found'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

        except Supp.MultipleObjectsReturned:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = 'Multiple Suplemental found'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

        except Exception as e:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = f'Error: {str(e)}'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportSuppStatusCigna(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        policyStatus = row[request.POST.get('policyStatus')]

        try:
            supp = Supp.objects.get(policyNumber=policyNumber)
            StatusSuplementals.objects.create(
                supp=supp,
                coverageMonth=datetime.now(),
                is_active=True if policyStatus == 'Active' else False
            )
            # Agregar el registro asociado al DataFrame
            matchedRecords.loc[len(matchedRecords)] = row

        except Supp.DoesNotExist:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = 'Suplemental not found'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

        except Supp.MultipleObjectsReturned:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = 'Multiple Suplemental found'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

        except Exception as e:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = f'Error: {str(e)}'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportSuppStatusUnited(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        holder = row[request.POST.get('holder')]
        policyStatus = row[request.POST.get('policyStatus')]

        if holder == 'Primary':
            try:
                supp = Supp.objects.get(policyNumber=policyNumber)
                PaymentsSuplementals.objects.create(
                    supp=supp,
                    coverageMonth=datetime.now(),
                    is_active=True if policyStatus == 'Active' else False
                )
                # Agregar el registro asociado al DataFrame
                matchedRecords.loc[len(matchedRecords)] = row

            except Supp.DoesNotExist:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Suplemental not found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Supp.MultipleObjectsReturned:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = 'Multiple Suplemental found'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

            except Exception as e:
                rowWithError = pd.Series(row)
                rowWithError['Error Reason'] = f'Error: {str(e)}'
                unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def getDetailReportSuppPaymentsCigna(request, dataFrame):
    # Crear un DataFrame vacío para almacenar los registros no asociados
    unmatchedRecords = pd.DataFrame(columns=[*dataFrame.columns, 'Error Reason'])
    matchedRecords = pd.DataFrame(columns=dataFrame.columns)

    # Iterate over rows
    for index, row in dataFrame.iterrows():
        policyNumber = row[request.POST.get('policyNumber')]
        coverageMonth = row[request.POST.get('coverageMonth')]
        commPaid = row[request.POST.get('commPaid')]

        try:
            supp = Supp.objects.get(policyNumber=policyNumber)
            PaymentsSuplementals.objects.create(
                supp=supp,
                coverageMonth=parseDateMDY(coverageMonth),
                is_active=True if commPaid > 0 else False
            )
            # Agregar el registro asociado al DataFrame
            matchedRecords.loc[len(matchedRecords)] = row

        except Supp.DoesNotExist:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = 'Suplemental not found'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

        except Supp.MultipleObjectsReturned:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = 'Multiple Suplemental found'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

        except Exception as e:
            rowWithError = pd.Series(row)
            rowWithError['Error Reason'] = f'Error: {str(e)}'
            unmatchedRecords.loc[len(unmatchedRecords)] = rowWithError

    return matchedRecords, unmatchedRecords

def classifyLabel(label):
    label = label.strip()
    if label.startswith("NCD"):
        return "DENTAL"
    elif label.startswith("VSP"):
        return "VISUAL"
    elif label.startswith("NCD") and label.endswith("VSP"):
        return "unknown"
    else:
        return "unknown"
        

def formatNumberPolicyOnlyPolicyNumber(policyNumber: str) -> str:
    return policyNumber

def formatNumberPolicyOnlySubcriberId(subscriberId: str) -> str:
    return subscriberId

def formatNumberPolicyBluecross(subscriberId: str):
    return f'000{subscriberId}'

def formatNumberPolicyMolina(subscriberId: str, state: str):
    policyNumer = re.findall(r'\d+\.?\d*', subscriberId)
    return f'{state}-{policyNumer}'

def formatNumberPolicyOscar(subscriberId: str):
    if pd.isna(subscriberId):
        raise ValueError("subscriberId is empty or NaN")
    return str(subscriberId)[:11]

def formatNumberPolicyCaresource(subscriberId: str):
    if pd.isna(subscriberId):
        raise ValueError("subscriberId is empty or NaN")
    return str(subscriberId)[:9]

def formatNumberPolicyUnited(subscriberId: str) -> str:
    if pd.isna(subscriberId):
        raise ValueError("subscriberId is empty or NaN")
    return str(subscriberId)[:9]


def formatPolicyNumberByCarrier(policyNumber: str, subscriberId: str, carrier: str, state: str) -> str:
    carrierLower = carrier.lower()

    if 'bluecross' in carrierLower:
        return formatNumberPolicyOnlyPolicyNumber(policyNumber)

    if 'blue cross' in carrierLower:
        return formatNumberPolicyBluecross(subscriberId)

    if 'caresource' in carrierLower:
        return formatNumberPolicyCaresource(subscriberId)

    if 'molina' in carrierLower:
        return formatNumberPolicyMolina(subscriberId, state)

    if 'oscar' in carrierLower:
        return formatNumberPolicyOscar(subscriberId)

    if 'united' in carrierLower:
        return formatNumberPolicyUnited(subscriberId)

    if any(keyword in carrierLower for keyword in ['aetna', 'ambetter', 'amerihealth', 'amgp', 'anthem', 'medica']):
        return formatNumberPolicyOnlySubcriberId(subscriberId)
        
    return subscriberId

def parseMonthYear(monthYearStr: str) -> date:
    try:
        parsed = datetime.strptime(monthYearStr, "%m/%Y")
    except ValueError:
        parsed = datetime.strptime(monthYearStr, "%b-%y")
    return date(parsed.year, parsed.month, 1)

def parseDateDMY(dateStr: str) -> date:
    # dateStr esperado en formato "22/02/2022"
    parsed = datetime.strptime(dateStr, "%d/%m/%Y")
    return date(parsed.year, parsed.month, parsed.day)

def parseDateMDY(dateStr: str) -> date:
    # dateStr esperado en formato "02/22/2022"
    parsed = datetime.strptime(dateStr, "%m/%d/%Y")
    return date(parsed.year, parsed.month, parsed.day)

def parseDateYMD(dateString: str) -> date:
    try:
        return datetime.strptime(dateString, "%Y-%m-%d").date()
    except ValueError:
        return None

def cleanForJson(dataframe):
    return dataframe.replace({np.nan: None}).to_dict(orient='records')

@csrf_exempt
def headerProcessor(request):
    if request.method == 'POST' and request.FILES.get('file'):
        uploaded_file = request.FILES['file']
        headers = []
        
        try:
            # Detectar la extensión del archivo
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            if file_extension == 'xlsx' or file_extension == 'xls':
                # Leer archivo Excel
                df = pd.read_excel(uploaded_file)
                headers = df.columns.tolist()
            elif file_extension == 'csv':
                # Leer archivo CSV
                df = pd.read_csv(uploaded_file)
                headers = df.columns.tolist()
            else:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Formato de archivo no soportado. Use Excel o CSV.'
                })
            return JsonResponse({
                'status': 'success',
                'headers': headers,
                'modalId':request.POST.get('reportingType')
            })
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error al procesar el archivo: {str(e)}'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': 'No se recibió ningún archivo'
    })