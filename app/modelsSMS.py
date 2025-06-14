from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from storages.backends.s3boto3 import S3Boto3Storage
from .models import Companies, Users, ObamaCare

# Create your models here.

class Contacts(models.Model):
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)  # Relación con la compañía
    name = models.CharField(max_length=50, null=True)
    phone_number = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField()

    class Meta:
        unique_together = ('company', 'phone_number')  # Restricción de unicidad por compañía y número de teléfono

    class Meta:
        db_table = 'sms_contacts'

    def __str__(self):
        return f'{self.name} - {self.phone_number} ({self.company.company_name})'
    
    def formatted_phone_number(self):
        if self.phone_number:
            phone_str = str(self.phone_number)
            formatted = f"+{phone_str[0]} ({phone_str[1:4]}) {phone_str[4:7]} {phone_str[7:]}"
            return formatted
        return None

class SecretKey(models.Model):
    contact = models.OneToOneField(Contacts, on_delete=models.CASCADE)
    secretKey = models.CharField(max_length=200)

    class Meta:
        db_table = 'sms_secretkey'

class Chat(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contacts, on_delete=models.CASCADE)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)  # Nueva relación
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('contact', 'company')  # Restringe a un solo chat por cliente y compañía

    def __str__(self):
        return f'{self.agent.username} - {self.contact.phone_number} ({self.company.company_name})'
    
    class Meta:
        db_table = 'sms_chat'

class Messages(models.Model):
    SENDER_TYPE_CHOICES = (
        ('A', 'Agent'),
        ('C', 'Client'),
    )
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE)
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES)
    sender = models.ForeignKey(Users, on_delete=models.CASCADE, null=True)
    message_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'sms_messages'

class FilesSMS(models.Model):
    file = models.FileField(
        upload_to='files',
        storage=S3Boto3Storage()
    )
    message = models.OneToOneField(Messages, on_delete=models.CASCADE)

    class Meta:
        db_table = 'sms_files'

class ContentTemplate(models.Model):
    contentTemplate = models.TextField()
    identification = models.CharField(max_length=100)

    class Meta:
        db_table = 'content_template'

class SmsTemplate(models.Model):
    contentTemplate = models.ForeignKey(ContentTemplate, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        db_table = 'sms_template'