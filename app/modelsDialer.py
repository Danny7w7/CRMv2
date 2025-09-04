# Standard Python libraries
import uuid

# Django core libraries
from django.db import models

# Application-specific imports
from .models import Users



class Campaign(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    max_concurrent_calls = models.IntegerField(default=3)  # Para no superar 5 CPS
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'dialer_campaigns'

class LeadsDialer(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='contacts')
    phone_number = models.CharField(max_length=20)
    address = models.CharField(max_length=255, blank=True, null=True)
    zipcode = models.CharField(max_length=10, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    last_contact = models.DateTimeField(null=True, blank=True)
    last_attempt = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.phone_number}"
    
    class Meta:
        db_table = 'dialer_leads'

class Agent(models.Model):
    AGENT_STATUS = [
        ('available', 'Disponible'),
        ('busy', 'Ocupado'),
        ('offline', 'Desconectado'),
        ('in_call', 'En Llamada')
    ]
    
    sip_username = models.CharField(max_length=100, blank=True, null=True)
    sip_password = models.CharField(max_length=100, blank=True, null=True)
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=AGENT_STATUS, default='offline')
    current_campaign = models.ForeignKey(Campaign, null=True, blank=True, on_delete=models.SET_NULL)
    current_call = models.ForeignKey('Call', null=True, blank=True, on_delete=models.SET_NULL, related_name='current_call')
    last_call = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.status}"
    
    class Meta:
        db_table = 'dialer_agents'

class Call(models.Model):
    CALL_STATUS = [
        ('initiated', 'Iniciada'),
        ('ringing', 'Timbrando'),
        ('answered', 'Contestada'),
        ('connected_to_agent', 'Conectada a Agente'),
        ('completed', 'Completada'),
        ('failed', 'Fallida'),
        ('no_answer', 'No Contesta'),
        ('busy', 'Ocupado')
    ]

    outcome = models.ForeignKey(
        "CallOutcome", 
        on_delete=models.SET_NULL,  # no borramos histórico si se elimina un outcome
        null=True, 
        blank=True,
        related_name="calls"
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact = models.ForeignKey(
        LeadsDialer, on_delete=models.CASCADE, 
        related_name="calls"
    )
    agent = models.ForeignKey(Agent, null=True, blank=True, on_delete=models.SET_NULL)
    telnyx_call_control_id = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=20, choices=CALL_STATUS, default='initiated')
    started_at = models.DateTimeField(auto_now_add=True)
    answered_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # en segundos
    
    def __str__(self):
        return f"Call {self.id} - {self.contact.phone_number}"
    
    class Meta:
        db_table = 'dialer_calls'
    
class CallOutcome(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    requiresCallback = models.BooleanField(default=False)
    isActive = models.BooleanField(default=True)
    createdAt = models.DateTimeField(auto_now_add=True)
    updatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'dialer_call_outcomes'
    