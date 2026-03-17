"""
Google Analytics 4 — Data API client.
Использует те же OAuth2 credentials что и GSC (общий GoogleOAuthToken).
Требует scope: https://www.googleapis.com/auth/analytics.readonly
"""
import logging
from datetime import timedelta, date
from django.conf import settings
from django.utils import timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .models import GoogleOAuthToken

logger = logging.getLogger('integrations')

GA4_SCOPE = 'https://www.googleapis.com/auth/analytics.readonly'
GSC_SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly'


def get_ga4_credentials(project):
    """
    Возвращает актуальные credentials с GA4 scope.
    Обновляет access_token если истёк.
    """
    try:
        token = project.google_token
    except GoogleOAuthToken.DoesNotExist:
        return None

    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri='https://oauth2.googleapis.com/token',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=[GSC_SCOPE, GA4_SCOPE],
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token.access_token = creds.token
        token.token_expiry = timezone.now() + timedelta(seconds=3600)
        token.save(update_fields=['access_token', 'token_expiry'])

    return creds


def fetch_ga4_data(project, days_back=30):
    """
    Запрашивает данные GA4 по дням и каналам за последние days_back дней.
    Возвращает список словарей:
      [{'date': date, 'channel': str, 'sessions': int, 'users': int,
        'new_users': int, 'pageviews': int, 'bounce_rate': float,
        'avg_session_duration': float}, ...]
    """
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest, DateRange, Dimension, Metric,
    )

    if not project.analytics_property:
        logger.warning('GA4: no property_id for project %s', project.name)
        return []

    creds = get_ga4_credentials(project)
    if not creds:
        logger.warning('GA4: no credentials for project %s', project.name)
        return []

    property_id = f'properties/{project.analytics_property}'
    end = timezone.now().date() - timedelta(days=1)   # вчера (GA4 не отдаёт сегодня)
    start = end - timedelta(days=days_back - 1)

    client = BetaAnalyticsDataClient(credentials=creds)
    request = RunReportRequest(
        property=property_id,
        dimensions=[
            Dimension(name='date'),
            Dimension(name='sessionDefaultChannelGroup'),
        ],
        metrics=[
            Metric(name='sessions'),
            Metric(name='totalUsers'),
            Metric(name='newUsers'),
            Metric(name='screenPageViews'),
            Metric(name='bounceRate'),
            Metric(name='averageSessionDuration'),
        ],
        date_ranges=[DateRange(
            start_date=start.strftime('%Y-%m-%d'),
            end_date=end.strftime('%Y-%m-%d'),
        )],
        limit=10000,
    )

    try:
        response = client.run_report(request)
    except Exception as e:
        logger.error('GA4 API error for %s: %s', project.name, e)
        raise

    rows = []
    for row in response.rows:
        raw_date = row.dimension_values[0].value   # "20260315"
        channel = row.dimension_values[1].value

        try:
            d = date(int(raw_date[:4]), int(raw_date[4:6]), int(raw_date[6:8]))
        except (ValueError, IndexError):
            continue

        rows.append({
            'date': d,
            'channel': channel,
            'sessions': int(row.metric_values[0].value or 0),
            'users': int(row.metric_values[1].value or 0),
            'new_users': int(row.metric_values[2].value or 0),
            'pageviews': int(row.metric_values[3].value or 0),
            'bounce_rate': round(float(row.metric_values[4].value or 0) * 100, 2),
            'avg_session_duration': round(float(row.metric_values[5].value or 0), 1),
        })

    logger.info('GA4 fetched %d rows for %s (%s to %s)',
                len(rows), project.name, start, end)
    return rows


def get_ga4_summary(project, days=28):
    """Суммарные метрики для карточки проекта на dashboard."""
    from apps.analytics.models import GA4Metrics
    from django.db.models import Sum, Avg
    since = timezone.now().date() - timedelta(days=days)
    qs = GA4Metrics.objects.filter(project=project, date__gte=since)
    agg = qs.aggregate(
        total_sessions=Sum('sessions'),
        total_users=Sum('users'),
        total_pageviews=Sum('pageviews'),
        avg_bounce=Avg('bounce_rate'),
    )
    return {
        'sessions':   agg['total_sessions'] or 0,
        'users':      agg['total_users'] or 0,
        'pageviews':  agg['total_pageviews'] or 0,
        'bounce_rate': round(agg['avg_bounce'] or 0, 1),
    }
