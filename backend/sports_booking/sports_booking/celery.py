from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sports_booking.settings')

app = Celery('sports_booking')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()

# Update the beat_schedule to include waitlist cleanup

app.conf.beat_schedule = {
    'cleanup-expired-locks-every-5-minutes': {
        'task': 'bookings.tasks.cleanup_expired_locks',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {'expires': 180}
    },
    'cleanup-old-waitlist-entries-daily': {
        'task': 'bookings.tasks.cleanup_old_waitlist_entries',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'options': {'expires': 3600}
    },
}

app.conf.timezone = 'Asia/Kolkata'
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60  # 30 minutes

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')