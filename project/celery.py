from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Establece el módulo de configuración predeterminado para el proyecto Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

app = Celery('project')

# Usa el sistema de configuración de Django para Celery
app.config_from_object('django.conf:settings', namespace='CELERY')

# Carga tareas de todas las aplicaciones registradas en Django.
app.autodiscover_tasks()

from celery.schedules import crontab

app.conf.beat_schedule = {
    'run-my-daily-task': {
        'task': 'app.tasks.my_daily_task',
        'schedule': crontab(minute=3, hour=17),  # Ejecutar a las 5:00 AM todos los días
    },
    'run-sms-payment-task': {
        'task': 'app.tasks.smsPayment',
        'schedule': crontab(minute=33, hour=9),  # Ejecutar a las 9:33 AM todos los días
    },
    'run-sms-report-task': {
        'task': 'app.tasks.reportBoosLapeira',
        'schedule': crontab(minute=2, hour=7, day_of_week='0,2-6'),  # Ejecutar a las 7 AM todos los días
    },
    'run-sms-reportTwo-task': {
        'task': 'app.tasks.enviar_pdf_por_email',
        'schedule': crontab(minute=1, hour=16, day_of_week='6'),  # Ejecutar a las 4PM todo los sabado
    },
    'run-sms-reportThree-task': {
        'task': 'app.tasks.test',
        'schedule': crontab(minute=59, hour=18),  # Ejecutar a las 4PM todo los sabado
    },
}