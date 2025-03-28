from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from storages.backends.s3boto3 import S3Boto3Storage

# Create your models here.

class Companies(models.Model):
    owner = models.CharField(max_length=250)
    company_name = models.CharField(max_length=250)
    phone_company = models.BigIntegerField()
    company_email = models.EmailField()
    is_active = models.BooleanField(default=True)
    remaining_balance = models.DecimalField(max_digits=20, decimal_places=6)

    class Meta:
        db_table = 'companies'

class Services(models.Model):
    name = models.CharField(max_length=100)
    cost = models.DecimalField(max_digits=10, decimal_places=4)
    description = models.TextField()

    def _str_(self):
        return self.name
    
    def formatCost(self):
        return "{:.2f}".format(self.cost)
    
    class Meta:
        db_table = 'services'

class Subscriptions(models.Model):
    PERIOD_CHOICES = (
        ('weekly', 'Weekly'),
        ('biweekly', 'Biweekly'),
        ('monthly', 'Monthly'),
        ('unique', 'Unique'),
    )

    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    service = models.ForeignKey(Services, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True) 
    auto_renew = models.BooleanField(default=False)
    renewal_period = models.CharField(max_length=10, choices=PERIOD_CHOICES, default='monthly')

    def _str_(self):
        return f'{self.company.name} - {self.service.name}'
    
    class Meta:
        db_table = 'subscriptions'

class Transactions(models.Model):
    TRANSACTION_TYPES = (
        ('recarga', 'Recarga'),
        ('descuento', 'Descuento'),
    )

    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remaining_balance = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now=True)

    def _str_(self):
        return f'{self.company.name} - {self.type} - {self.amount}'
    
    class Meta:
        db_table = 'transactions'


class Users(AbstractUser):

    ROLES_CHOICES = (
        ('A', 'Agent'),
        ('S', 'Supervisor'),
        ('C', 'Customer'),
        ('SUPP', 'Supplementary'),
        ('AU', 'Auditor'),
        ('TV', 'Tv'),
        ('Admin', 'Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLES_CHOICES)
    # Sobrescribimos solo el campo email
    email = models.EmailField(
        blank=True, 
        null=True,
        unique=False
    )
    assigned_phone = models.ForeignKey('app.Numbers', on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'users'
        
    def _str_(self):
        return self.username
    
    
    def formatted_phone_number(self):
        if self.assigned_phone and self.assigned_phone.phone_number:
            phone_str = str(self.assigned_phone.phone_number)
            formatted = f"+{phone_str[0]} ({phone_str[1:4]}) {phone_str[4:7]} {phone_str[7:]}"
            return formatted
        return None

class Clients(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    agent_usa = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.BigIntegerField()
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True) 
    address = models.CharField(max_length=255)
    zipcode = models.IntegerField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    county = models.CharField(max_length=100)
    sex = models.CharField(max_length=1) 
    date_birth = models.DateField()
    migration_status = models.CharField(max_length=100)
    social_security = models.CharField(max_length=9,null=True)
    type_sales = models.CharField(max_length=100)    
    is_active = models.BooleanField(default=True)  
    apply = models.BooleanField()
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'clients'

class Medicare(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    agent_usa = models.CharField(max_length=100)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.BigIntegerField()
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)    
    address = models.CharField(max_length=255)
    zipcode = models.IntegerField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    county = models.CharField(max_length=100)
    sex = models.CharField(max_length=1)   
    date_birth = models.DateField()
    dateMedicare = models.DateTimeField()
    migration_status = models.CharField(max_length=100)
    social_security = models.CharField(max_length=9,null=True) 
    nameAutorized = models.CharField(max_length=100, null= True)
    relationship = models.CharField(max_length=100, null= True) 
    status = models.CharField(max_length=100, null=True) 
    status_color = models.IntegerField(null = True)    
    is_active = models.BooleanField(default=True)  
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'medicare'

class ContactClient(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    phone = models.BooleanField(default=True) 
    email = models.BooleanField(default=True) 
    sms = models.BooleanField(default=True)  
    whatsapp = models.BooleanField(default=True) 

    class Meta:
        db_table = 'contactClient'

class OptionMedicare(models.Model):
    client = models.ForeignKey(Medicare, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    prescripcion  = models.BooleanField(default=True) 
    advantage = models.BooleanField(default=True) 
    dental = models.BooleanField(default=True) 
    complementarios  = models.BooleanField(default=True)  
    suplementarios = models.BooleanField(default=True)     

    class Meta:
        db_table = 'optionMedicare'

class Calls(models.Model):
    id_client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    id_agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    type = models.CharField(max_length=50)
    create_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'calls'

class Typifications(models.Model):
    id_call = models.ForeignKey(Calls, on_delete=models.CASCADE)
    content = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'typifications'

class ObamaCare(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE,related_name='agent_sale_aca')
    client = models.OneToOneField(Clients, on_delete=models.CASCADE,null=True)
    agent_usa = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True) 
    taxes = models.IntegerField()
    plan_name = models.CharField(max_length=200)
    carrier = models.CharField(max_length=200)
    premium = models.DecimalField(max_digits=10, decimal_places=2)
    profiling = models.CharField(max_length=200,default='NO')
    profiling_date = models.DateField(null=True)
    subsidy = models.DecimalField(max_digits=10, decimal_places=2,)
    ffm = models.BigIntegerField(null=True)
    required_bearing = models.BooleanField(default=False,null=True)
    date_bearing = models.DateField(null=True)
    doc_income = models.BooleanField(default=False,null=True)
    doc_migration = models.BooleanField(default=False,null=True)
    status = models.CharField(max_length=50,null=True)
    status_color = models.IntegerField(null = True)    
    policyNumber = models.CharField(max_length=200, null=True)
    work = models.CharField(max_length=50)
    date_effective_coverage = models.DateField(null=True)
    date_effective_coverage_end = models.DateField(null=True)
    observation = models.TextField(null=True)
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'obamacare'

class Dependents(models.Model):  
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True)  # Relación de muchos a uno
    name = models.CharField(max_length=200)
    apply = models.CharField(max_length=200)
    sex = models.CharField(max_length=1)
    kinship = models.CharField(max_length=100,null=True)
    date_birth = models.DateField(null=True)
    migration_status = models.CharField(max_length=50)
    type_police = models.TextField()

    class Meta:
        db_table = 'dependents'

class Supp(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='agent_sale_supp')
    agent_usa = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True) 
    effective_date = models.DateField()
    carrier = models.CharField(max_length=200)
    policy_type = models.CharField(max_length=100)
    premium = models.DecimalField(max_digits=10, decimal_places=2,)
    preventive = models.CharField(max_length=100)
    coverage = models.CharField(max_length=100)
    policyNumber = models.CharField(max_length=200, null=True)
    deducible = models.CharField(max_length=100)
    status = models.CharField(max_length=50,null=True)
    status_color = models.IntegerField(null = True)
    date_effective_coverage = models.DateField(null=True)
    date_effective_coverage_end = models.DateField(null=True)
    payment_type = models.CharField(max_length=50,null=True)
    observation = models.TextField(null=True)
    is_active = models.BooleanField(default=True)
    dependents = models.ManyToManyField(Dependents, related_name='SuppDependents')
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'supp'

class Payments(models.Model):
    obamaCare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    # amount = models.DecimalField(max_digits=6, decimal_places=2) esto lo guardo aqui para un futuro

    class Meta:
        db_table = 'payments'

class ObservationAgent(models.Model):
    id_client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    id_obamaCare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True, blank=True)
    id_supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null=True, blank=True)
    id_user = models.ForeignKey(Users, on_delete=models.CASCADE)
    content = models.TextField()

    class Meta:
        db_table = 'observationsAgents'

class ObservationCustomer(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)  
    type_police = models.CharField(max_length=20) 
    typeCall = models.CharField(max_length=20)   
    id_plan = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True) 
    typification = models.TextField()
    content = models.TextField()
    is_active = models.BooleanField(default=True) 

    class Meta:
        db_table = 'observationsCustomers'

class ObservationCustomerMedicare(models.Model):
    medicare = models.ForeignKey(Medicare, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)  
    typeCall = models.CharField(max_length=20, null=True)   
    created_at = models.DateTimeField(auto_now_add=True) 
    typification = models.TextField(null=True)
    content = models.TextField()

    class Meta:
        db_table = 'observationsCustomersMedicare'

class CustomerTracking(models.Model):
    id_obama = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True)
    id_supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null=True)
    cs4h = models.BooleanField(default=False)
    cs8d = models.BooleanField(default=False)
    cs3w = models.BooleanField(default=False)
    cs5w = models.BooleanField(default=False)
    activo = models.BooleanField(default=False)
    gossip = models.BooleanField(default=False)

    class Meta:
        db_table = 'customerTracking'

class Logs(models.Model):
    id_agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    datetime = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=255)

    class Meta:
        db_table = 'logs'

class Motivation(models.Model):
    content = models.TextField()

    class Meta:
        db_table = 'motivation'

class ClientAlert(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    name_client = models.CharField(max_length=255)
    phone_number = models.BigIntegerField()
    datetime = models.DateField()
    content = models.TextField()
    is_active = models.BooleanField(default=True)  
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'clientAlert'

class DropDownList(models.Model):
    profiling_obama = models.CharField(max_length=255,null=True)
    profiling_supp = models.CharField(max_length=255,null=True)
    status_bd = models.CharField(max_length=255,null=True)
    clave = models.TextField(null=True)  
    description = models.TextField(null=True) 

    class Meta:
        db_table = 'dropDownList'

class ExcelFileMetadata(models.Model):
    file_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    create_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'excelFileMetadata'

class BdExcel(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255,null=True)
    phone = models.BigIntegerField()
    address = models.CharField(max_length=255,null=True)
    city = models.CharField(max_length=200,null=True)
    state = models.CharField(max_length=200,null=True)
    zipCode = models.IntegerField(null=True)
    agent_id = models.IntegerField(null=True)
    excel_metadata = models.ForeignKey(ExcelFileMetadata,on_delete=models.CASCADE,related_name='records')
    is_sold = models.BooleanField(default=False)  # Campo booleano para indicar si está "solds"
    
    class Meta:
        db_table = 'bdExcel'

class ControlQuality(models.Model):
    agent_create = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='created_controls' )
    agent = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='assigned_controls')
    category = models.CharField(max_length=200, null=True)
    amount = models.BigIntegerField(null= True)
    date = models.DateField()
    findings = models.TextField(null= True)
    observation = models.TextField(null= True)
    create_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  

    class Meta:
        db_table = 'controlQuality'

class ControlCall(models.Model):
    agent_create = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='created_controls_call' )
    agent = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='assigned_controls_call',)
    daily = models.BigIntegerField()
    answered = models.BigIntegerField()
    mins = models.BigIntegerField()
    date = models.DateField()
    create_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'controlCall'

class CommentBD(models.Model):
    bd_excel = models.ForeignKey(BdExcel, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users, on_delete=models.CASCADE )
    excel_metadata = models.ForeignKey(ExcelFileMetadata,on_delete=models.CASCADE)
    content = models.TextField()
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'commentBD'

class DocumentsClient(models.Model):
    file = models.FileField(
        upload_to='consents',
        storage=S3Boto3Storage(),
        null=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)

    class Meta:
        db_table = 'documentsClient'

class Consents(models.Model):
    pdf = models.FileField(
        upload_to='DocumentsClient',
        storage=S3Boto3Storage(),
        null=True)
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null = True)
    medicare = models.ForeignKey(Medicare, on_delete=models.CASCADE, null = True)
    signature = models.FileField(
        upload_to='SignatureConsents',
        storage=S3Boto3Storage(),
        null=True)

    class Meta:
        db_table = 'consents'


class IncomeLetter(models.Model):
    pdf = models.FileField(
        upload_to='incomeLetter',
        storage=S3Boto3Storage(),
        null=True)
    signature = models.FileField(
        upload_to='SignatureLetterIncome',
        storage=S3Boto3Storage(),
        null=True)
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)

    class Meta:
        db_table = 'incomeLetter'

class TemporaryToken(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null = True)
    contact = models.ForeignKey('app.Contacts', on_delete=models.CASCADE, null = True)
    medicare = models.ForeignKey(Medicare, on_delete=models.CASCADE, null = True)
    token = models.TextField()  # Guardar el token firmado
    expiration = models.DateTimeField()
    is_active = models.BooleanField(default=True)  # Para invalidar manualmente

    def is_expired(self):
        return timezone.now() > self.expiration

    def __str__(self):
        return f"Temporary URL for {self.client.first_name} (Active: {self.is_active})"

    class Meta:
        db_table = 'temporaryToken'

class DocumentObama(models.Model):
    file = models.FileField(
        upload_to='DocumentObama',
        storage=S3Boto3Storage())
    obama = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE )   
    name =  models.CharField(max_length=255, default="Unnamed Document")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documentObama'

class LettersCard(models.Model):
    obama = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE )    
    letters = models.BooleanField(default=False) 
    dateLetters = models.DateField(null=True)
    card = models.BooleanField(default=False) 
    dateCard = models.DateField(null=True)

    class Meta:
        db_table = 'lettersCard'

class AppointmentClient(models.Model):
    obama = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE )    
    appointment = models.TextField() 
    dateAppointment = models.DateField()
    timeAppointment = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointmentClient'

class UserCarrier(models.Model):
    obama = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE)    
    username_carrier = models.CharField(max_length=200,null=True)
    password_carrier = models.CharField(max_length=200,null=True)
    dateUserCarrier = models.DateField(null=True)

    class Meta:
        db_table = 'userCarrier'

class CustomerRedFlag(models.Model):
    obama = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE, related_name='created_flags')    
    clave = models.CharField(max_length=100)  
    description = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)
    agent_completed = models.ForeignKey(Users,on_delete=models.CASCADE, related_name='completed_flags', null=True)    
    date_completed = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'customerRedFlag'


from .modelsSMS import *
