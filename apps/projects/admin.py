from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'domain', 'platform', 'is_active', 'created_at')
    list_filter = ('platform', 'is_active')
    search_fields = ('name', 'domain')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Основное', {
            'fields': ('name', 'slug', 'domain', 'platform', 'is_active'),
        }),
        ('Google интеграции', {
            'fields': ('search_console_property', 'analytics_property', 'sitemap_url'),
        }),
        ('Git', {
            'fields': ('local_repo_path', 'git_remote_url'),
        }),
        ('Служебное', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )
