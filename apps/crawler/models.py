from django.db import models
from apps.projects.models import Project


class CrawlSession(models.Model):
    """Один запуск краулера для проекта."""
    STATUS_CHOICES = [
        ('running', 'В процессе'),
        ('done',    'Завершён'),
        ('error',   'Ошибка'),
    ]
    project      = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='crawl_sessions')
    started_at   = models.DateTimeField(auto_now_add=True)
    finished_at  = models.DateTimeField(null=True, blank=True)
    status       = models.CharField(max_length=10, choices=STATUS_CHOICES, default='running')
    pages_found  = models.PositiveIntegerField(default=0)
    pages_crawled = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.project.name} — {self.started_at:%Y-%m-%d %H:%M} ({self.status})'

    @property
    def duration_seconds(self):
        if self.finished_at:
            return (self.finished_at - self.started_at).seconds
        return None


class CrawlResult(models.Model):
    """Результат краулинга одной страницы."""
    SEVERITY_ERROR   = 'error'
    SEVERITY_WARNING = 'warning'
    SEVERITY_OK      = 'ok'

    session          = models.ForeignKey(CrawlSession, on_delete=models.CASCADE, related_name='results')
    project          = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='crawl_results')
    url              = models.URLField(max_length=2048)
    status_code      = models.PositiveSmallIntegerField(null=True, blank=True)
    title            = models.CharField(max_length=512, blank=True)
    meta_description = models.TextField(blank=True)
    h1               = models.CharField(max_length=512, blank=True)
    canonical        = models.URLField(max_length=2048, blank=True)
    load_time_ms     = models.PositiveIntegerField(null=True, blank=True)
    word_count       = models.PositiveIntegerField(default=0)
    images_missing_alt = models.PositiveSmallIntegerField(default=0)
    internal_links   = models.PositiveSmallIntegerField(default=0)
    # SEO issue flags
    issue_title_missing   = models.BooleanField(default=False)
    issue_title_short     = models.BooleanField(default=False)
    issue_title_long      = models.BooleanField(default=False)
    issue_desc_missing    = models.BooleanField(default=False)
    issue_desc_short      = models.BooleanField(default=False)
    issue_desc_long       = models.BooleanField(default=False)
    issue_h1_missing      = models.BooleanField(default=False)
    issue_h1_multiple     = models.BooleanField(default=False)
    issue_canonical_diff  = models.BooleanField(default=False)
    issue_broken          = models.BooleanField(default=False)  # 4xx/5xx
    crawled_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('session', 'url')]
        ordering = ['url']

    def __str__(self):
        return f'[{self.status_code}] {self.url}'

    @property
    def severity(self):
        if self.issue_broken or self.issue_title_missing or self.issue_h1_missing:
            return self.SEVERITY_ERROR
        if (self.issue_title_short or self.issue_title_long or
                self.issue_desc_missing or self.issue_desc_short or
                self.issue_desc_long or self.issue_h1_multiple or
                self.issue_canonical_diff or self.images_missing_alt > 0):
            return self.SEVERITY_WARNING
        return self.SEVERITY_OK

    @property
    def issues_list(self):
        issues = []
        if self.issue_broken:          issues.append(('error',   f'Страница недоступна ({self.status_code})'))
        if self.issue_title_missing:   issues.append(('error',   'Нет title'))
        if self.issue_h1_missing:      issues.append(('error',   'Нет H1'))
        if self.issue_title_short:     issues.append(('warning', f'Title короткий ({len(self.title)} симв.)'))
        if self.issue_title_long:      issues.append(('warning', f'Title длинный ({len(self.title)} симв.)'))
        if self.issue_desc_missing:    issues.append(('warning', 'Нет meta description'))
        if self.issue_desc_short:      issues.append(('warning', f'Description короткий ({len(self.meta_description)} симв.)'))
        if self.issue_desc_long:       issues.append(('warning', f'Description длинный ({len(self.meta_description)} симв.)'))
        if self.issue_h1_multiple:     issues.append(('warning', 'Несколько H1'))
        if self.issue_canonical_diff:  issues.append(('warning', 'Canonical ≠ URL'))
        if self.images_missing_alt:    issues.append(('warning', f'{self.images_missing_alt} изобр. без alt'))
        return issues

