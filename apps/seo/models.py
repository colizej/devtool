from django.db import models
from apps.projects.models import Project


class SeoIssue(models.Model):
    ISSUE_TYPES = [
        ('low_ctr',       'Низкий CTR'),
        ('low_position',  'Низкая позиция'),
        ('no_clicks',     'Нет кликов'),
    ]
    PRIORITY = [
        ('high',   'Высокий'),
        ('medium', 'Средний'),
        ('low',    'Низкий'),
    ]
    STATUS = [
        ('new',         'Новая'),
        ('important',   'Важно'),
        ('in_progress', 'В работе'),
        ('fixed',       'Исправлено'),
        ('ignored',     'Игнорировать'),
    ]

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name='seo_issues', verbose_name='Проект',
    )
    issue_type = models.CharField(max_length=20, choices=ISSUE_TYPES, verbose_name='Тип')
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium', verbose_name='Приоритет')
    query = models.CharField(max_length=500, blank=True, verbose_name='Запрос')
    page = models.URLField(max_length=1000, blank=True, verbose_name='Страница')
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0, verbose_name='CTR %')
    position = models.FloatField(default=0.0, verbose_name='Позиция')
    potential_clicks = models.IntegerField(default=0, verbose_name='Потенциал (клики)')
    status = models.CharField(
        max_length=20, choices=STATUS, default='new', verbose_name='Статус',
        db_index=True,
    )
    note = models.TextField(blank=True, verbose_name='Заметка')
    detected_at = models.DateField(auto_now_add=True, verbose_name='Дата обнаружения')
    updated_at = models.DateField(auto_now=True, verbose_name='Обновлено')

    class Meta:
        verbose_name = 'SEO Проблема'
        verbose_name_plural = 'SEO Проблемы'
        ordering = ['-potential_clicks']
        indexes = [
            models.Index(fields=['project', 'issue_type']),
            models.Index(fields=['project', 'priority']),
        ]

    def __str__(self):
        return f'[{self.get_priority_display()}] {self.get_issue_type_display()} — {self.query or self.page}'
