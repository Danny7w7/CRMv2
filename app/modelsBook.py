from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from storages.backends.s3boto3 import S3Boto3Storage
from .models import Companies, Users, ObamaCare

# Create your models here.


    # models.py
from django.db import models

class pdfBook(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(
        upload_to='book',
        storage=S3Boto3Storage(),
        null=True
    ) # S3 manejará el almacenamiento
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_converted = models.BooleanField(default=False) 
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)  

    def __str__(self):
        return self.title

    def get_s3_url(self):
        return self.file.url  # Esto ya devuelve la URL pública o firmada del archivo

    class Meta:
        db_table = 'book_pdf'

class BookReading(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    book = models.ForeignKey(pdfBook, on_delete=models.CASCADE)
    page = models.IntegerField()
    time_spent = models.IntegerField(help_text="Tiempo en segundos")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'book_reading'
