from __future__ import absolute_import, unicode_literals
from celery import Celery
import urllib.parse
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'be_django_rest_api.settings')

from django.conf import settings

app = Celery('be_django_rest_api')

DB_USER = settings.DATABASES['default']['USER']
DB_PW = urllib.parse.quote_plus(settings.DATABASES['default']['PASSWORD'])
DB_NAME = settings.DATABASES['default']['NAME']

ResBackend = 'db+postgresql+psycopg2://' + DB_USER + ':' + DB_PW + '@localhost/' + DB_NAME

app.conf.update(
    broker_url='amqp://localhost',
    result_backend=ResBackend,
    task_track_started=True,
)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
