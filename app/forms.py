import datetime
from django import forms
from app.models import *

class ClientForm(forms.ModelForm):
    class Meta:
        model = Clients
        fields = '__all__'
        exclude = ['agent','date_birth','social_security','company','created_at']

class ClientLifeForm(forms.ModelForm):
    class Meta:
        model = ClientsLifeInsurance
        fields = '__all__'
        exclude = ['agent','date_birth','social_security','company','created_at', 'observation','is_active','status','status_color','date_effective_coverage','date_effective_coverage_end','payment_type','policyNumber']

class ClientFormAssure(forms.ModelForm):
    class Meta:
        model = ClientsAssure
        fields = '__all__'
        exclude = ['agent','date_birth','social_security','company','created_at','status','status_color','date_effective_coverage','date_effective_coverage_end','payment_type','policyNumber']

class ClientMedicareForm(forms.ModelForm):
    class Meta:
        model = Medicare
        fields = '__all__'
        exclude = ['agent','date_birth','social_security','dateMedicare','status','status_color','company','created_at','nameAutorized','relationship']

class ObamaForm(forms.ModelForm):
    class Meta:
        model = ObamaCare
        fields = '__all__'
        exclude = ['client','agent','is_active','profiling','profiling_date','ffm','required_bearing','date_bearing','status','npm','date_effective_coverage','date_effective_coverage_end','password_carrier','username_carrier','policyNumber','status_color','observation','company']

class SuppForm(forms.ModelForm):
    class Meta:
        model = Supp
        fields = '__all__'
        exclude = ['client','agent','is_active','status','date_effective_coverage','date_effective_coverage_end','payment_type','status_color','policyNumber','observation','effective_date','dependents','company']

class DepentForm(forms.ModelForm):
    class Meta:
        model = Dependents
        fields = '__all__'
        exclude = ['client','obamacare','date_birth']

class PaymentsForm(forms.ModelForm):
    class Meta:
        model = Payments
        fields = '__all__'
        exclude = ['agent']

class ClientAlertForm(forms.ModelForm):
    class Meta:
        model = ClientAlert
        fields = '__all__'
        exclude = ['agent','company']

class ExcelUploadForm(forms.Form):
    file = forms.FileField(label="Subir archivo Excel", 
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx, .xls'  # Limita a archivos Excel
        }))

class ControlQualityForm(forms.ModelForm):
    class Meta:
        model = ControlQuality
        fields = '__all__'
        exclude = ['agent_create','observation','amount','category']

    #cambiamos formato de la fecha para guardarla como se debe en la BD ya que la obtenes en formato USA
    def clean_date(self):
        date_input = self.cleaned_data['date']
        
        # Si el input ya es un objeto de fecha, lo devolvemos tal cual
        if isinstance(date_input, datetime.date):
            return date_input

        # Si es una cadena, lo convertimos al formato adecuado
        try:
            return datetime.strptime(date_input, '%m/%d/%Y').date()
        except ValueError:
            raise forms.ValidationError('Formato de fecha inválido. Use MM/DD/YYYY.')

class ControlCallForm(forms.ModelForm):
    class Meta:
        model = ControlCall
        fields = '__all__'
        exclude = ['agent_create']

    #cambiamos formato de la fecha para guardarla como se debe en la BD ya que la obtenes en formato USA
    def clean_date(self):
        date_input = self.cleaned_data['date']
        
        # Si el input ya es un objeto de fecha, lo devolvemos tal cual
        if isinstance(date_input, datetime.date):
            return date_input

        # Si es una cadena, lo convertimos al formato adecuado
        try:
            return datetime.strptime(date_input, '%m/%d/%Y').date()
        except ValueError:
            raise forms.ValidationError('Formato de fecha inválido. Use MM/DD/YYYY.')

class ServicesForm(forms.ModelForm):
    class Meta:
        model = Services
        fields = '__all__'

    