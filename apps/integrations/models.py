from django.db import models
from django.utils import timezone
from apps.projects.models import Project


class GoogleOAuthToken(models.Model):
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='google_token',
        verbose_name='Проект',
    )
    access_token = models.TextField(verbose_name='Access Token')
    refresh_token = models.TextField(verbose_name='Refresh Token')
    token_expiry = models.DateTimeField(verbose_name='Срок действия')
    scopes = models.TextField(verbose_name='Scopes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Google OAuth Token'
        verbose_name_plural = 'Google OAuth Tokens'

    def __str__(self):
        return f'Token: {self.project.name}'

    def is_expired(self):
        return timezone.now() >= self.token_expiry
