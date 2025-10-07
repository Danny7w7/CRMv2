from django.db import models
from storages.backends.s3boto3 import S3Boto3Storage
from .models import Companies, Users
import filetype

# Create your models here.

class Contacts_whatsapp(models.Model):
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)  # Relación con la compañía
    name = models.CharField(max_length=50, null=True)
    phone_number = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField()

    class Meta:
        unique_together = ('company', 'phone_number')  # Restricción de unicidad por compañía y número de teléfono

    class Meta:
        db_table = 'contacts_whatsapp'

    def __str__(self):
        return f'{self.name} - {self.phone_number} ({self.company.company_name})'
    
    def formatted_phone_number(self):
        if self.phone_number:
            phone_str = str(self.phone_number)
            formatted = f"+{phone_str[0]} ({phone_str[1:4]}) {phone_str[4:7]} {phone_str[7:]}"
            return formatted
        return None

class Chat_whatsapp(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    contact = models.ForeignKey(Contacts_whatsapp, on_delete=models.CASCADE)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)  # Nueva relación
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message = models.DateTimeField(null=True)

    class Meta:
        unique_together = ('contact', 'company')  # Restringe a un solo chat por cliente y compañía

    def __str__(self):
        return f'{self.agent.username} - {self.contact.phone_number} ({self.company.company_name})'
    
    class Meta:
        db_table = 'chat_whatsapp'

class Messages_whatsapp(models.Model):
    SENDER_TYPE_CHOICES = (
        ('A', 'Agent'),
        ('C', 'Client'),
    )
    chat = models.ForeignKey(Chat_whatsapp, on_delete=models.CASCADE)
    sender_type = models.CharField(max_length=20, choices=SENDER_TYPE_CHOICES)
    sender = models.ForeignKey(Users, on_delete=models.CASCADE, null=True)
    message_content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'messages_whatsapp'

class Files_whatsapp(models.Model):
    file = models.FileField(
        upload_to='files',
        storage=S3Boto3Storage()
    )
    message = models.OneToOneField(Messages_whatsapp, on_delete=models.CASCADE)
    content_type = models.CharField(max_length=100, null=True, blank=True)  # nuevo campo

    def save(self, *args, **kwargs):
            # Primero guarda el archivo en S3
            super().save(*args, **kwargs)

            # Luego detecta tipo solo si no está seteado
            if not self.content_type and self.file:
                try:
                    # Leer primeros bytes del archivo real
                    self.file.open('rb')
                    data = self.file.read(2048)
                    self.file.close()

                    kind = filetype.guess(data)
                    if kind:
                        self.content_type = kind.mime
                    else:
                        self.content_type = 'application/octet-stream'

                    super().save(update_fields=['content_type'])
                except Exception as e:
                    print(f"⚠️ Error detectando tipo de archivo: {e}")

    class Meta:
        db_table = 'files_whatsapp'

