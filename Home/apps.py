from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from .jobs import SendWeatherForcast
from datetime import datetime
from django.conf import settings
import requests


def awaker():
    print("hello awaker")
    res = requests.request("GET", settings.HOSTNAME)

class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Home'

    def ready(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(SendWeatherForcast, 'cron', hour=0, minute=0)

        if settings.AWAKE == '1':
            scheduler.add_job(awaker, 'cron', minute='*/10')
        
        scheduler.start()
