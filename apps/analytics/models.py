from django.db import models
from apps.projects.models import Project


class SearchConsoleMetrics(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='gsc_metrics',
        verbose_name='Проект',
    )
    date = models.DateField(verbose_name='Дата')
    query = models.CharField(max_length=500, blank=True, verbose_name='Запрос')
    page = models.URLField(max_length=1000, blank=True, verbose_name='Страница')
    clicks = models.IntegerField(default=0, verbose_name='Клики')
    impressions = models.IntegerField(default=0, verbose_name='Показы')
    ctr = models.FloatField(default=0.0, verbose_name='CTR')
    position = models.FloatField(default=0.0, verbose_name='Позиция')

    class Meta:
        verbose_name = 'GSC Метрика'
        verbose_name_plural = 'GSC Метрики'
        ordering = ['-date', 'position']
        indexes = [
            models.Index(fields=['project', 'date']),
            models.Index(fields=['project', 'query']),
            models.Index(fields=['project', 'page']),
        ]
        unique_together = [['project', 'date', 'query', 'page']]

    def __str__(self):
        return f'{self.project.name} | {self.date} | {self.query[:50]}'


class GA4Metrics(models.Model):
    """Daily Google Analytics 4 metrics per project."""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='ga4_metrics',
        verbose_name='Проект',
    )
    date = models.DateField(verbose_name='Дата')
    sessions = models.IntegerField(default=0, verbose_name='Сессии')
    users = models.IntegerField(default=0, verbose_name='Пользователи')
    new_users = models.IntegerField(default=0, verbose_name='Новые пользователи')
    pageviews = models.IntegerField(default=0, verbose_name='Просмотры')
    bounce_rate = models.FloatField(default=0.0, verbose_name='Отказы (%)')
    avg_session_duration = models.FloatField(default=0.0, verbose_name='Ср. время сессии (сек)')
    # Источник: organic, direct, referral, social и т.д.
    channel = models.CharField(max_length=100, blank=True, default='', verbose_name='Канал')

    class Meta:
        verbose_name = 'GA4 Метрика'
        verbose_name_plural = 'GA4 Метрики'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['project', 'date']),
            models.Index(fields=['project', 'channel']),
        ]
        unique_together = [['project', 'date', 'channel']]

    def __str__(self):
        return f'{self.project.name} | {self.date} | {self.channel or "all"}'
