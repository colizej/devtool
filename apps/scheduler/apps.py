from django.apps import AppConfig


class SchedulerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scheduler'

    def ready(self):
        import sys
        # Запускаем только при реальном runserver, не при migrate/check/etc.
        # Двойной вызов ready() при --noreload исключаем через RUN_MAIN
        import os
        if os.environ.get('RUN_MAIN') != 'true':
            return
        if 'runserver' not in sys.argv:
            return

        from django_apscheduler.jobstores import DjangoJobStore
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from .tasks import import_gsc_all_projects, import_ga4_all_projects
        import logging

        logger = logging.getLogger('scheduler')

        try:
            scheduler = BackgroundScheduler()
            scheduler.add_jobstore(DjangoJobStore(), 'default')
            scheduler.add_job(
                import_gsc_all_projects,
                trigger=CronTrigger(hour=6, minute=0),
                id='import_gsc_daily',
                name='Ежедневный импорт GSC',
                replace_existing=True,
                jobstore='default',
            )
            scheduler.add_job(
                import_ga4_all_projects,
                trigger=CronTrigger(hour=6, minute=15),
                id='import_ga4_daily',
                name='Ежедневный импорт GA4',
                replace_existing=True,
                jobstore='default',
            )
            scheduler.start()
            logger.info('APScheduler started: GSC at 06:00, GA4 at 06:15')
        except Exception as e:
            logger.error('APScheduler failed to start: %s', e)
