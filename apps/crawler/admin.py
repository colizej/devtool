from django.contrib import admin
from .models import CrawlSession, CrawlResult


@admin.register(CrawlSession)
class CrawlSessionAdmin(admin.ModelAdmin):
    list_display = ['project', 'started_at', 'status', 'pages_crawled', 'pages_found']
    list_filter = ['status', 'project']
    readonly_fields = ['started_at', 'finished_at']


@admin.register(CrawlResult)
class CrawlResultAdmin(admin.ModelAdmin):
    list_display = ['url', 'status_code', 'severity', 'title', 'load_time_ms']
    list_filter = ['project', 'status_code', 'issue_broken']
    search_fields = ['url', 'title']
    readonly_fields = ['crawled_at']
