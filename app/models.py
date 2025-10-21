from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from storages.backends.s3boto3 import S3Boto3Storage
from .managers import VisibilityManager
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Module(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'module'

class Companies(models.Model):
    owner = models.CharField(max_length=250)
    company_name = models.CharField(max_length=250)
    phone_company = models.BigIntegerField()
    company_email = models.EmailField()
    zipcode = models.IntegerField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    county = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    remaining_balance = models.DecimalField(max_digits=20, decimal_places=6)
    modules = models.ManyToManyField('Module', blank=True)

    class Meta:
        db_table = 'companies'

class Invoice(models.Model):
    pdf = models.FileField(
        upload_to='Invoice',
        storage=S3Boto3Storage(),
        null=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoice'

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

class Numbers(models.Model):
    phone_number = models.BigIntegerField()  
    company = models.ForeignKey(Companies, on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True) 
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'numbers'

class USAgent(models.Model):
    name = models.CharField(max_length=50)
    company = models.ManyToManyField(Companies)

    class Meta:
        db_table = 'us_agents'

    def getFirstName(self):
        return self.name.strip().split()[0] if self.name.strip() else ""
    
class Numbers_whatsapp(models.Model):
    phone_number = models.BigIntegerField()  
    company = models.ForeignKey(Companies, on_delete=models.CASCADE) 
    created_at = models.DateTimeField(auto_now_add=True) 
    is_active = models.BooleanField(default=True)  

    class Meta:
        db_table = 'numbers_whatsapp' 

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
    assigned_phone = models.ForeignKey(Numbers, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_phone_whatsapp = models.ForeignKey(Numbers_whatsapp, on_delete=models.SET_NULL, null=True, blank=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    usaAgents = models.ManyToManyField(USAgent)
    agent_seguro = models.ManyToManyField(USAgent, related_name='agent_seguro_users', blank=True)
    
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
    
    def formatted_phone_number_whatsapp(self):
        if self.assigned_phone_whatsapp and self.assigned_phone_whatsapp.phone_number:
            phone_str = str(self.assigned_phone_whatsapp.phone_number)
            formatted = f"+{phone_str[0]} ({phone_str[1:4]}) {phone_str[4:7]} {phone_str[7:]}"
            return formatted
        return None
    
class UserPreference(models.Model):
    user = models.OneToOneField(Users, on_delete=models.CASCADE)
    darkMode = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_preference'

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
    county = models.CharField(max_length=100, null=True)
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

    def _str_(self):
        return f'{self.first_name} {self.last_name} - {self.phone_number}'

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
    objects = VisibilityManager()

    class Meta:
        db_table = 'medicare'

class ClientsLifeInsurance(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    agent_usa = models.CharField(max_length=100)
    full_name = models.CharField(max_length=200)
    phone_number = models.BigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True) 
    address = models.CharField(max_length=255)
    zipcode = models.IntegerField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)
    county = models.CharField(max_length=100, null=True)
    sex = models.CharField(max_length=1) 
    date_birth = models.DateField()
    social_security = models.CharField(max_length=9,null=True)
    full_name_beneficiary = models.CharField(max_length=200)
    phone_number_beneficiary = models.BigIntegerField()
    observation = models.TextField(null=True)
    status = models.CharField(max_length=50,null=True)
    status_color = models.IntegerField(null = True)
    date_effective_coverage = models.DateField(null=True)
    date_effective_coverage_end = models.DateField(null=True)
    policyNumber = models.CharField(max_length=200, null=True)
    payment_type = models.CharField(max_length=50,null=True)
    is_active = models.BooleanField(default=True)  
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    objects = VisibilityManager()
    face_amount = models.IntegerField()
    addicional_protector = models.IntegerField()
    premium = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'clients_life_insurance'

    def _str_(self):
        return f'{self.full_name} - {self.phone_number}'

class AskLifeInsurance(models.Model):
    ask_es =models.TextField(null=True)
    ask_en = models.TextField(null=True)

    class Meta:
        db_table = 'ask_life_insurance'

class AnswerLifeInsurance(models.Model):
    client = models.ForeignKey(ClientsLifeInsurance, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    ask = models.ForeignKey(AskLifeInsurance, on_delete=models.CASCADE)
    answer = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'answer_life_insurance'

class ContactClient(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    phone = models.BooleanField(default=True) 
    email = models.BooleanField(default=True) 
    sms = models.BooleanField(default=True)  
    whatsapp = models.BooleanField(default=True) 

    class Meta:
        db_table = 'contact_client'

class OptionMedicare(models.Model):
    client = models.ForeignKey(Medicare, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    prescripcion  = models.BooleanField(default=True) 
    advantage = models.BooleanField(default=True) 
    dental = models.BooleanField(default=True) 
    complementarios  = models.BooleanField(default=True)  
    suplementarios = models.BooleanField(default=True)     

    class Meta:
        db_table = 'option_medicare'

class ObamaCare(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE,related_name='agent_sale_aca')
    client = models.ForeignKey(Clients, on_delete=models.CASCADE,null=True)
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
    objects = VisibilityManager()
    tipe_sale = models.CharField(max_length=10, default='V')

    class Meta:
        db_table = 'obamacare'

class Dependents(models.Model):  
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    obamacare = models.ManyToManyField( 'ObamaCare', related_name='dependents_many')
    name = models.CharField(max_length=200)
    apply = models.CharField(max_length=200)
    sex = models.CharField(max_length=1)
    policyNumber = models.CharField(max_length=50, null=True)
    kinship = models.CharField(max_length=100,null=True)
    date_birth = models.DateField(null=True)
    migration_status = models.CharField(max_length=50)
    type_police = models.TextField()
    is_active_obama = models.BooleanField(default=False)
    is_active_supp = models.BooleanField(default=False)

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
    objects = VisibilityManager()

    class Meta:
        db_table = 'supp'

class ChangeDateLogs(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null=True)
    reason = models.TextField(null=False)
    old_date = models.DateField()
    new_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    authorized_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, related_name='date_logs_created')
    authorized_by = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, related_name='date_logs_authorized')
    approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'change_date_logs'

class ChangeAgentLogs(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null=True)
    reason = models.TextField(null=False)
    old_agent = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, related_name='old_agent')
    new_agent = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, related_name='new_agent')
    created_at = models.DateTimeField(auto_now_add=True)
    authorized_at = models.DateTimeField(null=True)
    created_by = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, related_name='agent_logs_created')
    authorized_by = models.ForeignKey(Users, on_delete=models.CASCADE, null=True, related_name='agent_logs_authorized')
    approved = models.BooleanField(null=True)

    class Meta:
        db_table = 'change_agent_logs'

class ClientsAssure(models.Model):
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
    county = models.CharField(max_length=100, null=True)
    nationality = models.CharField(max_length=200)
    sex = models.CharField(max_length=1) 
    date_birth = models.DateField()
    migration_status = models.CharField(max_length=100)
    social_security = models.CharField(max_length=9,null=True)
    status = models.CharField(max_length=50,null=True)
    status_color = models.IntegerField(null = True)
    date_effective_coverage = models.DateField(null=True)
    date_effective_coverage_end = models.DateField(null=True)
    policyNumber = models.CharField(max_length=200, null=True)
    payment_type = models.CharField(max_length=50,null=True)
    is_active = models.BooleanField(default=True)  
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    objects = VisibilityManager()

    class Meta:
        db_table = 'Clients_assure'

    def _str_(self):
        return f'{self.first_name} {self.last_name} - {self.phone_number}'
    
class DependentsAssure(models.Model):  
    client = models.ForeignKey(ClientsAssure, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    date_birth = models.DateField(null=True)
    sex = models.CharField(max_length=1) 
    country = models.CharField(max_length=200)
    kinship = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        db_table = 'dependents_assure'

class StatusSuplementals(models.Model):
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE)
    coverageMonth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField()

    class Meta:
        db_table = 'status_suplementals'

class PaymentsSuplementals(models.Model):
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE)
    coverageMonth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField()

    class Meta:
        db_table = 'payments_suplementals'

class PaymentsOneil(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agency = models.CharField(max_length=50)
    coverageMonth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    payday = models.DateField()
    payable = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        db_table = 'payments_oneil'

class PaymentsCarriers(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    carrier = models.CharField(max_length=50)
    coverageMonth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False) #Esto es si el cliente esta activo o no

    class Meta:
        db_table = 'payments_carriers'

class PaymentsSherpa(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    coverageMonth = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False) #Esto es si el cliente esta activo o no

    class Meta:
        db_table = 'payments_sherpa'

class Payments(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    month = models.CharField(max_length=20)
    typePayment = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    # amount = models.DecimalField(max_digits=6, decimal_places=2) esto lo guardo aqui para un futuro

    class Meta:
        db_table = 'payments'

class ObservationAgent(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    obamaCare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True, blank=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null=True, blank=True)
    assure = models.ForeignKey(ClientsAssure, on_delete=models.CASCADE, null=True, blank=True)
    life_insurance = models.ForeignKey(ClientsLifeInsurance, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'observations_agents'

class ObservationCustomer(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)  
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null=True)
    assure = models.ForeignKey(ClientsAssure, on_delete=models.CASCADE, null=True, blank=True)
    life_insurance = models.ForeignKey(ClientsLifeInsurance, on_delete=models.CASCADE, null=True, blank=True)
    typeCall = models.CharField(max_length=20)   
    created_at = models.DateTimeField(auto_now_add=True) 
    typification = models.TextField()
    content = models.TextField()
    is_active = models.BooleanField(default=True) 

    class Meta:
        db_table = 'observations_customers'

class ObservationCustomerMedicare(models.Model):
    medicare = models.ForeignKey(Medicare, on_delete=models.CASCADE)
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)  
    typeCall = models.CharField(max_length=20, null=True)   
    created_at = models.DateTimeField(auto_now_add=True) 
    typification = models.TextField(null=True)
    content = models.TextField()

    class Meta:
        db_table = 'observations_customers_medicare'

class Motivation(models.Model):
    content = models.TextField()

    class Meta:
        db_table = 'motivation'

class ClientAlert(models.Model):
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    name_client = models.CharField(max_length=255)
    phone_number = models.BigIntegerField()
    datetime = models.DateField()
    time = models.TimeField()
    content = models.TextField()
    is_active = models.BooleanField(default=True)  
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)  

    class Meta:
        db_table = 'client_alert'

class DropDownList(models.Model):
    profiling_obama = models.CharField(max_length=255,null=True)
    profiling_supp = models.CharField(max_length=255,null=True)
    status_bd = models.CharField(max_length=255,null=True)
    clave = models.TextField(null=True)  
    description = models.TextField(null=True) 
    service_company = models.TextField(null=True) 
    errores_omision = models.TextField(null=True)

    class Meta:
        db_table = 'drop_down_list'

class ExcelFileMetadata(models.Model):
    file_name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    create_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'excel_file_metadata'

class BasePerson(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255, null=True)
    phone = models.BigIntegerField()
    address = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    zipCode = models.IntegerField(null=True)
    agent_id = models.IntegerField(null=True)
    is_sold = models.BooleanField(default=False)

    class Meta:
        abstract = True  # No se crea tabla para esta clase

class BdExcel(BasePerson):
    excel_metadata = models.ForeignKey(
        ExcelFileMetadata,
        on_delete=models.CASCADE,
        related_name='records'
    )

    class Meta:
        db_table = 'bd_excel'

class Leads(BasePerson):
    email = models.EmailField(max_length=254)
    class Meta:
        db_table = 'leads'

class LeadExtraField(models.Model):
    lead = models.ForeignKey(Leads, on_delete=models.CASCADE, related_name='extra_fields')
    field_name = models.CharField(max_length=255)
    field_value = models.TextField()

    class Meta:
        db_table = 'lead_extra_fields'

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
        db_table = 'control_quality'

class ControlCall(models.Model):
    agent_create = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='created_controls_call' )
    agent = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='assigned_controls_call',)
    daily = models.BigIntegerField()
    answered = models.BigIntegerField()
    mins = models.BigIntegerField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'control_call'

class CommentBD(models.Model):
    bd_excel = models.ForeignKey(BdExcel, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users, on_delete=models.CASCADE )
    excel_metadata = models.ForeignKey(ExcelFileMetadata,on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comment_bd'

class DocumentsClient(models.Model):
    file = models.FileField(
        upload_to='DocumentsClient',
        storage=S3Boto3Storage(),
        null=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'documents_client'

class Consents(models.Model):
    pdf = models.FileField(
        upload_to='Consents',
        storage=S3Boto3Storage(),
        null=True)
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null = True)
    medicare = models.ForeignKey(Medicare, on_delete=models.CASCADE, null = True)
    lifeInsurance = models.ForeignKey(ClientsLifeInsurance, on_delete=models.CASCADE, null = True)
    signature = models.FileField(
        upload_to='SignatureConsents',
        storage=S3Boto3Storage(),
        null=True)
        
    created_at = models.DateTimeField(auto_now_add=True) 

    class Meta:
        db_table = 'consents'

class IncomeLetter(models.Model):
    pdf = models.FileField(
        upload_to='IncomeLetter',
        storage=S3Boto3Storage(),
        null=True)
    signature = models.FileField(
        upload_to='SignatureIncomeLetter',
        storage=S3Boto3Storage(),
        null=True)
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'income_letter'

class IncomeLetterFFM(models.Model):
    pdf = models.FileField(
        upload_to='IncomeLetterFFM',
        storage=S3Boto3Storage(),
        null=True)
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'incomeLetter_ffm'

class Complaint(models.Model):
    pdf = models.FileField(
        upload_to='Complaint',
        storage=S3Boto3Storage(),
        null=True)
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent = models.TextField()
    npn = models.TextField(null= True)
    signature = models.FileField(
    upload_to='SignatureComplaint',
    storage=S3Boto3Storage(),
    null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'complaint'

class EmailFraudReportRecord(models.Model):
    body = models.TextField()
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    first_consent = models.ForeignKey(Consents, on_delete=models.CASCADE, related_name='first_consent')
    last_consent = models.ForeignKey(Consents, on_delete=models.CASCADE, related_name='last_consent')
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_fraud_report_record'

class TemporaryToken(models.Model):
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null = True)
    contact = models.ForeignKey('app.Contacts', on_delete=models.CASCADE, null = True)
    medicare = models.ForeignKey(Medicare, on_delete=models.CASCADE, null = True)
    life_insurance = models.ForeignKey(ClientsLifeInsurance, on_delete=models.CASCADE, null = True)
    token = models.TextField()  # Guardar el token firmado
    expiration = models.DateTimeField()
    is_active = models.BooleanField(default=True)  # Para invalidar manualmente

    def is_expired(self):
        return timezone.now() > self.expiration

    class Meta:
        db_table = 'temporary_token'

class DocumentObamaSupp(models.Model):
    file = models.FileField(
        upload_to='DocumentObamaSupp',
        storage=S3Boto3Storage())
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null=True)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, null=True)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE )   
    name =  models.CharField(max_length=255, default="Unnamed Document")
    created_at = models.DateTimeField(auto_now_add=True) 
    typePlan = models.CharField(max_length=20, default='OBAMACARE')  

    class Meta:
        db_table = 'document_obama_supp'

class LettersCard(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE )    
    letters = models.BooleanField(default=False) 
    dateLetters = models.DateField(null=True)
    card = models.BooleanField(default=False) 
    dateCard = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'letters_card'

class AppointmentClient(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE)    
    appointment = models.TextField() 
    dateAppointment = models.DateField()
    timeAppointment = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'appointment_client'

class UserCarrier(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE)    
    username_carrier = models.CharField(max_length=200,null=True)
    password_carrier = models.CharField(max_length=200,null=True)
    dateUserCarrier = models.DateField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_carrier'

class CustomerRedFlag(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE, related_name='created_flags')    
    clave = models.CharField(max_length=100)  
    description = models.TextField() 
    created_at = models.DateTimeField(auto_now_add=True)
    agent_completed = models.ForeignKey(Users,on_delete=models.CASCADE, related_name='completed_flags', null=True)    
    date_completed = models.DateField(null=True, blank=True)

    class Meta:
        db_table = 'customer_red_flag'

class PaymentDate(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null= True)
    assure = models.ForeignKey(ClientsAssure, on_delete=models.CASCADE, null=True, blank=True)
    life_insurance = models.ForeignKey(ClientsLifeInsurance, on_delete=models.CASCADE, null=True, blank=True)
    payment_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    agent_create = models.ForeignKey(Users,on_delete=models.CASCADE)   

    class Meta:
        db_table = 'payment_date'

class AgentTicketAssignment(models.Model):
    obamacare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null= True)
    assure = models.ForeignKey(ClientsAssure, on_delete=models.CASCADE, null=True, blank=True)
    agent_create = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='agent_create' )
    agent_customer = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='agent_customer')
    content = models.TextField()
    response = models.TextField()
    status = models.CharField(max_length=100)  
    created_at = models.DateTimeField(auto_now_add=True)
    end_date = models.DateField(null=True)
    is_active = models.BooleanField(default=True)  
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'agent_ticket_assignment'

class KeyAccess(models.Model):
    user = models.ForeignKey(Users,  on_delete=models.CASCADE)
    password = models.CharField(max_length=200)  
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  

    class Meta:
        db_table = 'key_access'

class KeyAccessLog(models.Model):
    user = models.ForeignKey(Users, on_delete=models.SET_NULL, null=True, blank=True)
    client = models.ForeignKey(Clients, on_delete=models.SET_NULL, null=True, blank=True)
    password = models.ForeignKey(KeyAccess, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)  

    class Meta:
        db_table = 'key_access_log'

class FinallExpenses(models.Model):

    first_name = models.CharField(max_length=100, verbose_name="Nombre")
    last_name = models.CharField(max_length=100, verbose_name="Apellido")
    phone_number = models.BigIntegerField()
    date_birth = models.DateField(verbose_name="Fecha de nacimiento")
    
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Género")
    RELATIONSHIP_CHOICES = [
        ('SELF', 'SELF'),
        ('AUNT', 'AUNT'),
        ('BROTHER', 'BROTHER'),
        ('CHILD', 'CHILD'),
        ('COUSIN', 'COUSIN'),
        ('FATHER', 'FATHER'),
        ('FIANCE', 'FIANCE'),
        ('GRANDC', 'GRANDCHILD'),
        ('GRANDP', 'GRANDPARENT'),
        ('MOTHER', 'MOTHER'),
        ('NEPHEW', 'NEPHEW'),
        ('NIECE', 'NIECE'),
        ('PWROATNY', 'POWER OF ATTORNEY'),
        ('SISTER', 'SISTER'),
        ('SPOUSE', 'SPOUSE'),
        ('UNCLE', 'UNCLE'),
    ]
    relationship = models.CharField(max_length=10, choices=RELATIONSHIP_CHOICES, verbose_name="Relación con el asegurado")
    current_city = models.CharField(max_length=100, verbose_name="Ciudad actual")
    STATE_CHOICES = [
        ('AL', 'Alabama'),
        ('AR', 'Arkansas'),
        ('CA', 'California'),
        ('DC', 'District of Columbia'),
        ('DE', 'Delaware'),
        ('FL', 'Florida'),
        ('GA', 'Georgia'),
        ('ID', 'Idaho'),
        ('IL', 'Illinois'),
        ('IN', 'Indiana'),
        ('KS', 'Kansas'),
        ('KY', 'Kentucky'),
        ('LA', 'Louisiana'),
        ('MI', 'Michigan'),
        ('MN', 'Minnesota'),
        ('MO', 'Missouri'),
        ('MS', 'Mississippi'),
        ('NC', 'North Carolina'),
        ('ND', 'North Dakota'),
        ('NE', 'Nebraska'),
        ('NM', 'New Mexico'),
        ('NV', 'Nevada'),
        ('OH', 'Ohio'),
        ('OK', 'Oklahoma'),
        ('PA', 'Pennsylvania'),
        ('SC', 'South Carolina'),
        ('TN', 'Tennessee'),
        ('TX', 'Texas'),
        ('UT', 'Utah'),
        ('VA', 'Virginia'),
        ('WV', 'West Virginia'),
    ]
    current_state = models.CharField(max_length=2, choices=STATE_CHOICES, verbose_name="Estado actual")
    
    # Preguntas de hospitalización (Step 2)
    hospitalized_currently = models.BooleanField(verbose_name="¿Hospitalizado actualmente?")
    hospitalized_10_years = models.BooleanField(verbose_name="¿Hospitalizado 2+ veces en 10 años?")
    hospitalized_5_years = models.BooleanField(verbose_name="¿Hospitalizado 2+ veces en 5 años?")
    hospitalized_3_years = models.BooleanField(verbose_name="¿Hospitalizado 2+ veces en 3 años?")
    hospitalized_6_months = models.BooleanField(verbose_name="¿Hospitalizado 2+ veces en 6 meses?")
    
    # Preguntas sobre cáncer/derrames (Step 3)
    cancer_stroke_history = models.BooleanField(verbose_name="¿Historial de cáncer o derrame?")
    cancer_free_2_years = models.BooleanField(verbose_name="¿Libre de cáncer/derrame 2 años?")
    cancer_free_5_years = models.BooleanField(verbose_name="¿Libre de cáncer/derrame 5 años?")
    cancer_free_10_years = models.BooleanField(verbose_name="¿Libre de cáncer/derrame 10 años?")
    
    # Preguntas sobre tabaco (Step 4)
    tobacco_use = models.BooleanField(verbose_name="¿Usa tabaco/nicotina?")
    tobacco_bp_10_years = models.BooleanField(verbose_name="¿Tabaco o presión alta en 10 años?")
    tobacco_5_years = models.BooleanField(verbose_name="¿Usó tabaco en 5 años?")
    tobacco_12_months = models.BooleanField(verbose_name="¿Usó tabaco en 12 meses?")
    
    # Datos físicos (Step 5)
    height_ft = models.DecimalField(
        max_digits=3, 
        decimal_places=1,
        validators=[MinValueValidator(3.0), MaxValueValidator(8.5)],
        verbose_name="Altura (pies)"
    )
    weight_lbs = models.PositiveIntegerField(
        validators=[MinValueValidator(50), MaxValueValidator(500)],
        verbose_name="Peso (libras)"
    )

    created_at = models.DateTimeField(auto_now_add=True) 
    agent = models.ForeignKey(Users, on_delete=models.CASCADE)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)  

    class Meta:
        db_table = 'finall_expenses'

class ControlQuestions(models.Model):

    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    questions = models.TextField()
    is_active = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    
    class Meta:
        db_table = 'control_questions'

class QuestionTracking(models.Model):

    control_question = models.ForeignKey(ControlQuestions, on_delete=models.CASCADE)
    answer = models.CharField(max_length=100)
    control_agent = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='control_agent')
    sales_agent = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='sales_agent')
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)
    obs = models.TextField(null=True)


    class Meta:
        db_table = 'question_tracking'

class ErroresOmision(models.Model):

    agentCreated = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='agente_creacion')
    agent = models.ForeignKey(Users, on_delete=models.CASCADE,  related_name='agente_asignacion')
    client = models.ForeignKey(Clients, on_delete=models.CASCADE)
    eoID = models.ForeignKey(DropDownList, on_delete=models.CASCADE)
    eo = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    company = models.ForeignKey(Companies, on_delete=models.CASCADE)

    class Meta:
        db_table = 'errores_omision'

class CignaSuplemental(models.Model):

    pdf = models.FileField(
        upload_to='CignaSuplemental',
        storage=S3Boto3Storage(),
        null=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE)
    signature = models.FileField( upload_to='SignatureCignaSuplemental', storage=S3Boto3Storage(), null=True)
    is_active = models.BooleanField(default=True) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'cigna_suplemental'

class CignaSuplementalDraft(models.Model):
    supp = models.OneToOneField("Supp", on_delete=models.CASCADE)
    data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "cigna_suplemental_drafts"

class PlanMonitoring(models.Model):

    obamaCare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE, null=True, blank=True)
    supp = models.ForeignKey(Supp, on_delete=models.CASCADE, null=True, blank=True)
    assure = models.ForeignKey(ClientsAssure, on_delete=models.CASCADE, null=True, blank=True)
    life_insurance = models.ForeignKey(ClientsLifeInsurance, on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "plan_monitoring"

class PlanMonitoringPost(models.Model):

    obamaCare = models.ForeignKey(ObamaCare, on_delete=models.CASCADE)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "plan_monitoring_post"


from django.db import models

class FacebookAccount(models.Model):
    # Representa la conexión de una página de Facebook para un cliente
    owner_name = models.CharField(max_length=150, help_text="Nombre de la empresa/cliente")
    page_id = models.CharField(max_length=100, unique=True)
    page_name = models.CharField(max_length=200)
    page_access_token = models.TextField()
    connected_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.owner_name} — {self.page_name} ({self.page_id})"

class FacebookLead(models.Model):
    facebook_account = models.ForeignKey(FacebookAccount, on_delete=models.CASCADE, related_name='leads')
    leadgen_id = models.CharField(max_length=100)
    created_time = models.DateTimeField(null=True, blank=True)
    raw_payload = models.JSONField(null=True, blank=True)
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Lead {self.leadgen_id} — {self.facebook_account.page_name}"


from .modelsSMS import *
from .modelsWhatsapp import *
from .modelsDialer import *
