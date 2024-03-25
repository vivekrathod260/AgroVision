from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler
from .jobs import SendWeatherForcast
from datetime import datetime

class HomeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Home'

    def ready(self):
        scheduler = BackgroundScheduler()
        scheduler.add_job(SendWeatherForcast, 'cron', minute='*/1')
        scheduler.start()
