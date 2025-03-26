from django.contrib import admin
from .models import Clients
from .modelsSMS import Contacts

# Register your models here.
admin.site.register(Clients)
admin.site.register(Contacts)