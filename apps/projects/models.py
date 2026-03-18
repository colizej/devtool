from django.db import models
from django.utils.text import slugify


class Project(models.Model):
    PLATFORM_CHOICES = [
        ('django',    'Django'),
        ('wordpress', 'WordPress'),
        ('nextjs',    'Next.js'),
        ('nuxt',      'Nuxt.js'),
        ('shopify',   'Shopify'),
        ('hugo',      'Hugo'),
        ('jekyll',    'Jekyll'),
        ('laravel',   'Laravel'),
        ('other',     'Other'),
    ]

    name = models.CharField(max_length=200, verbose_name='Название')
    slug = models.SlugField(unique=True, blank=True, verbose_name='Slug')
    domain = models.CharField(max_length=200, verbose_name='Домен', help_text='Например: prava.be')
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        default='other',
        verbose_name='Платформа',
    )
    sitemap_url = models.URLField(
        blank=True,
        verbose_name='Sitemap URL',
        help_text='Например: https://prava.be/sitemap.xml',
    )
    search_console_property = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='GSC Property',
        help_text='Например: sc-domain:prava.be',
    )
    analytics_property = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='GA4 Property ID',
        help_text='Например: 123456789',
    )
    local_repo_path = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Путь к локальному репозиторию',
        help_text='Например: /Users/user/projects/prava',
    )
    git_remote_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='Git Remote URL',
        help_text='Например: git@github.com:user/prava.git',
    )
    admin_url = models.URLField(
        max_length=500,
        blank=True,
        verbose_name='URL Admin панели',
        help_text='Например: https://prava.be/admin/ или https://clikme.ru/admin/index.php',
    )
    is_active = models.BooleanField(default=True, verbose_name='Активен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')

    class Meta:
        verbose_name = 'Проект'
        verbose_name_plural = 'Проекты'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} ({self.domain})'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('projects:detail', kwargs={'slug': self.slug})
