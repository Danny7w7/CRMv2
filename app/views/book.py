
import json
import tempfile
import os

import boto3
from pdf2image import convert_from_path

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count

from app.modelsBook import *

@login_required(login_url='/login')  
def uploadBook(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        file = request.FILES.get('file')
        company = request.user.company

        if not file:
            return render(request, 'book/uploadBook.html', {'error': 'No se envió ningún archivo'})

        pdf = pdfBook.objects.create(title=title, file=file, company=company)

        # Convertir a imágenes y subirlas a S3
        convertPDFandUpload(pdf)

        # Marcar como convertido
        pdf.is_converted = True
        pdf.save()

        return redirect('bookList')  # Cambia por tu ruta de redirección después de subir

    return render(request, 'book/uploadBook.html')

def convertPDFandUpload(pdf_document):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )
    bucket = settings.AWS_STORAGE_BUCKET_NAME

    # 1. Crear archivo temporal para el PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf_file:
        temp_pdf_path = tmp_pdf_file.name

    # 2. Descargar desde S3 al archivo temporal
    s3.download_file(bucket, pdf_document.file.name, temp_pdf_path)

    # 3. Convertir a imágenes
    pages = convert_from_path(temp_pdf_path, dpi=150)

    image_keys = []

    for index, page in enumerate(pages, start=1):
        # 4. Crear archivo temporal para cada imagen
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_img_file:
            temp_img_path = tmp_img_file.name

        page.save(temp_img_path, 'PNG')

        # 5. Subir a S3
        image_key = f"book_pages/{pdf_document.id}/page_{index}.png"
        s3.upload_file(temp_img_path, bucket, image_key)

        image_keys.append(image_key)

        # 6. Eliminar imagen temporal
        os.remove(temp_img_path)

    # 7. Eliminar el PDF temporal
    os.remove(temp_pdf_path)

    return image_keys

@login_required(login_url='/login')  
def bookList(request):
    
    company =  request.user.company

    if request.user.is_superuser:
        books = pdfBook.objects.all()
    else:
        books = pdfBook.objects.filter(company_id = company, is_astive = True)

    return render(request, 'book/bookList.html', {'books': books})

def listImagenesBook(pdf_id):
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    bucket = settings.AWS_STORAGE_BUCKET_NAME
    prefix = f'book_pages/{pdf_id}/'

    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)

    if 'Contents' not in response:
        return []

    return sorted([obj['Key'] for obj in response['Contents']])

def generarPresignedUrl(key, expiration=3600):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )

    bucket_name = settings.AWS_STORAGE_BUCKET_NAME

    url = s3_client.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': bucket_name, 'Key': key},
        ExpiresIn=expiration
    )

    return url

@login_required(login_url='/login')  
def bookPages(request, pdf_id):
    pdf_document = pdfBook.objects.get(id=pdf_id)

    image_keys = listImagenesBook(pdf_id)
    imagenes = [generarPresignedUrl(key) for key in image_keys]

    page = int(request.GET.get('page', 1))
    total_pages = len(imagenes)

    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages

    imagen = imagenes[page - 1] if imagenes else None

    return render(request, 'book/bookPages.html', {
        'imagen': imagen,
        'page': page,
        'total_pages': total_pages,
        'pdf_id': pdf_id,
    })

@csrf_exempt
def saveTime(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        BookReading.objects.create(
            user=request.user,
            book=pdfBook.objects.get(id=data.get('book_id')),
            page=data['page'],
            time_spent=data['time_spent']
        )
        return JsonResponse({'status': 'ok'})

@login_required(login_url='/login')  
def toggleBook(request, book_id):
    
    # Obtener el cliente por su ID
    book = get_object_or_404(pdfBook, id=book_id)
    
    # Cambiar el estado de is_active (True a False o viceversa)
    book.is_active = not book.is_active
    book.save()  # Guardar los cambios en la base de datos
    
    # Redirigir de nuevo a la página actual con un parámetro de éxito
    return redirect('bookList')

@login_required(login_url='/login')  
def bookReport(request):

    readingUser = BookReading.objects.select_related('book').filter(book__is_active = True).values('user__username').annotate(
        total_time=Sum('time_spent')
    ).order_by('-total_time')

    readingPage = BookReading.objects.select_related('book').filter(book__is_active = True).values('book__title', 'page').annotate(
        avg_time=Sum('time_spent') / Count('id')
    ).order_by('book__title', 'page')

    booksRead = pdfBook.objects.filter(is_active = True).annotate(
        total_time=Sum('bookreading__time_spent'), total_lecturas=Count('bookreading')
    ).order_by('-total_time')

    readingDay = BookReading.objects.select_related('book').filter(book__is_active = True).values('date').annotate(
        total_time=Sum('time_spent')
    ).order_by('date')

    readingsDayUsers = BookReading.objects.select_related('book').filter(book__is_active = True).values('date', 'user__username').annotate(
        total_time=Sum('time_spent')
    ).order_by('date', 'user__username')

    readingsDayUserBook = BookReading.objects.select_related('book').filter(book__is_active = True).values('date', 'user__username', 'book__title').annotate(
        total_time=Sum('time_spent')
    ).order_by('date', 'user__username', 'book__title')

    return render(request, 'book/bookReports.html', {
        'readingUser': readingUser,
        'readingPage': readingPage,
        'booksRead': booksRead,
        'readingDay': readingDay,
        'readingsDayUsers': readingsDayUsers,
        'readingsDayUserBook': readingsDayUserBook,
    })




