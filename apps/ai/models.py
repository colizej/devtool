from django.db import models
from apps.projects.models import Project


class AIRecommendation(models.Model):
    """Хранит AI-рекомендацию для конкретного URL проекта."""

    REC_TYPES = [
        ('title',       'Title'),
        ('description', 'Meta Description'),
        ('h1',          'H1'),
        ('ctr_analysis','CTR Analysis'),
    ]

    project     = models.ForeignKey(Project, on_delete=models.CASCADE,
                                    related_name='ai_recommendations')
    url         = models.URLField(max_length=1000)
    rec_type    = models.CharField(max_length=20, choices=REC_TYPES)
    # Входные данные, которые были переданы в промпт
    input_data  = models.JSONField(default=dict)
    # Ответ AI в виде словаря (варианты, объяснение)
    result      = models.JSONField(default=dict)
    tokens_used = models.IntegerField(default=0)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AI Рекомендация'
        verbose_name_plural = 'AI Рекомендации'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'url']),
            models.Index(fields=['project', 'rec_type']),
        ]

    def __str__(self):
        return f'[{self.get_rec_type_display()}] {self.url} ({self.created_at:%Y-%m-%d})'
