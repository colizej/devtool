import logging
from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Sum, Avg, Count
from .models import Project
from apps.integrations.gsc import get_gsc_summary

logger = logging.getLogger(__name__)


@login_required
def dashboard(request):
    """Main dashboard — list of all active projects with GSC summary."""
    projects = Project.objects.filter(is_active=True)
    projects_data = []
    for project in projects:
        gsc = get_gsc_summary(project)
        try:
            connected = project.google_token is not None
        except Exception:
            connected = False
        projects_data.append({
            'project': project,
            'clicks': gsc['clicks'],
            'impressions': gsc['impressions'],
            'connected': connected,
        })
    return render(request, 'projects/dashboard.html', {'projects_data': projects_data})


@login_required
@ensure_csrf_cookie
def project_detail(request, slug):
    """Project detail page with GSC data, tabs and date filter."""
    from apps.analytics.models import SearchConsoleMetrics
    import json as _json
    project = get_object_or_404(Project, slug=slug, is_active=True)
    try:
        connected = project.google_token is not None
    except Exception:
        connected = False

    # Фильтр дат: GET ?days=7|30|90, default 30
    try:
        days = int(request.GET.get('days', 30))
        if days not in (7, 30, 90):
            days = 30
    except (ValueError, TypeError):
        days = 30

    since = timezone.now().date() - timedelta(days=days)
    active_tab = request.GET.get('tab', 'overview')

    qs = SearchConsoleMetrics.objects.filter(project=project, date__gte=since)

    # Сводка
    summary = qs.aggregate(
        total_clicks=Sum('clicks'),
        total_impressions=Sum('impressions'),
        avg_position=Avg('position'),
    )

    # Данные по дням для графика (Overview)
    daily = (
        qs.values('date')
        .annotate(clicks=Sum('clicks'), impressions=Sum('impressions'))
        .order_by('date')
    )
    chart_labels = _json.dumps([str(r['date']) for r in daily])
    chart_clicks = _json.dumps([r['clicks'] for r in daily])
    chart_impressions = _json.dumps([r['impressions'] for r in daily])

    # Топ запросов (вкладка Запросы)
    top_queries = (
        qs.values('query')
        .annotate(clicks=Sum('clicks'), impressions=Sum('impressions'), avg_position=Avg('position'), avg_ctr=Avg('ctr'))
        .order_by('-clicks')[:50]
    )

    # Топ страниц (вкладка Страницы)
    top_pages = (
        qs.values('page')
        .annotate(clicks=Sum('clicks'), impressions=Sum('impressions'), avg_position=Avg('position'))
        .order_by('-clicks')[:50]
    )

    last_import = SearchConsoleMetrics.objects.filter(
        project=project
    ).values_list('date', flat=True).order_by('-date').first()

    # GA4 — вкладка Traffic
    from apps.analytics.models import GA4Metrics
    import json as _json2
    ga4_has_data = GA4Metrics.objects.filter(project=project).exists()
    ga4_connected = bool(project.analytics_property)

    # Данные по дням для GA4 графика (все каналы суммарно)
    ga4_daily = (
        GA4Metrics.objects.filter(project=project, date__gte=since)
        .values('date')
        .annotate(
            s=Sum('sessions'),
            u=Sum('users'),
            pv=Sum('pageviews'),
        )
        .order_by('date')
    )
    ga4_chart_labels      = _json2.dumps([str(r['date']) for r in ga4_daily])
    ga4_chart_sessions    = _json2.dumps([r['s'] for r in ga4_daily])
    ga4_chart_users       = _json2.dumps([r['u'] for r in ga4_daily])
    ga4_chart_pageviews   = _json2.dumps([r['pv'] for r in ga4_daily])

    # Разбивка по каналам за период
    ga4_channels = (
        GA4Metrics.objects.filter(project=project, date__gte=since)
        .values('channel')
        .annotate(
            sessions=Sum('sessions'),
            users=Sum('users'),
            pageviews=Sum('pageviews'),
        )
        .order_by('-sessions')
    )

    # Summary GA4
    from apps.integrations.ga4 import get_ga4_summary
    ga4_summary = get_ga4_summary(project, days=days)

    # SEO Issues
    from apps.seo.models import SeoIssue
    issue_type_filter = request.GET.get('issue_type', '')
    seo_qs = SeoIssue.objects.filter(project=project)
    if issue_type_filter:
        seo_qs = seo_qs.filter(issue_type=issue_type_filter)
    seo_issues = list(seo_qs.order_by('-potential_clicks')[:200])
    seo_issues_count = SeoIssue.objects.filter(project=project).count()

    # Подсчёт по типам для фильтр-кнопок
    from django.db.models import Count
    type_counts_qs = (
        SeoIssue.objects.filter(project=project)
        .values('issue_type')
        .annotate(cnt=Count('id'))
    )
    type_label_map = dict(SeoIssue.ISSUE_TYPES)
    issue_type_counts = [
        (row['issue_type'], type_label_map.get(row['issue_type'], row['issue_type']))
        for row in type_counts_qs
        if row['cnt'] > 0
    ]

    # Crawler
    from apps.crawler.models import CrawlSession, CrawlResult, BrokenLink
    crawl_session = CrawlSession.objects.filter(project=project).first()
    crawl_results = CrawlResult.objects.filter(session=crawl_session) if crawl_session else []
    broken_links = BrokenLink.objects.filter(session=crawl_session).order_by('broken_url') if crawl_session else []

    return render(request, 'projects/detail.html', {
        'project': project,
        'connected': connected,
        'days': days,
        'active_tab': active_tab,
        'tabs': [
            ('overview',  'Overview'),
            ('queries',   'Запросы'),
            ('pages',     'Страницы'),
            ('traffic',   'Трафик'),
            ('seo',       'SEO Issues'),
            ('crawler',   'Crawler'),
            ('ai',        'AI Report'),
            ('git',       'Git Sync'),
        ],
        'days_options': [7, 30, 90],
        'summary': summary,
        'chart_labels': chart_labels,
        'chart_clicks': chart_clicks,
        'chart_impressions': chart_impressions,
        'top_queries': top_queries,
        'top_pages': top_pages,
        'last_import': last_import,
        'has_data': qs.exists(),
        'seo_issues': seo_issues,
        'seo_issues_count': seo_issues_count,
        'issue_type_counts': issue_type_counts,
        # GA4
        'ga4_connected': ga4_connected,
        'ga4_has_data': ga4_has_data,
        'ga4_summary': ga4_summary,
        'ga4_channels': ga4_channels,
        'ga4_chart_labels': ga4_chart_labels,
        'ga4_chart_sessions': ga4_chart_sessions,
        'ga4_chart_users': ga4_chart_users,
        'ga4_chart_pageviews': ga4_chart_pageviews,
        # Crawler
        'crawl_session': crawl_session,
        'crawl_results': crawl_results,
        'broken_links': broken_links,
    })
