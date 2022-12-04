from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from .jobs import SendWeatherForcast
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
# from django.core.management.base import BaseCommand
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution
from django_apscheduler import util


def start():
    scheduler = BackgroundScheduler()

    scheduler.add_job(
    SendWeatherForcast,
    # 'interval',
    # seconds=10,
    # trigger=CronTrigger(second="*/20"),
    trigger=CronTrigger(day='*/1',hour=0,minute=0,second = 0),
    # trigger=CronTrigger(hour=0,minute=0,second = 0),
    id="my_job",  # The `id` assigned to each job MUST be unique
    max_instances=1,
    replace_existing=True,
    )

    scheduler.start()
