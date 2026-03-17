import logging
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from .models import GoogleOAuthToken

logger = logging.getLogger('integrations')

SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def get_credentials(project):
    """Возвращает актуальные Google credentials для проекта, обновляя если нужно."""
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
        scopes=SCOPES,
    )

    if token.is_expired():
        try:
            creds.refresh(Request())
            token.access_token = creds.token
            token.token_expiry = timezone.now() + timedelta(seconds=3600)
            token.save(update_fields=['access_token', 'token_expiry', 'updated_at'])
            logger.info('Token refreshed for project %s', project.name)
        except Exception as e:
            logger.error('Token refresh failed for project %s: %s', project.name, e)
            return None

    return creds


def fetch_gsc_data(project, start_date, end_date, row_limit=25000):
    """
    Загружает данные из GSC для проекта за указанный период.
    Возвращает список строк с query+page+clicks+impressions+ctr+position.
    """
    creds = get_credentials(project)
    if not creds:
        logger.warning('No valid credentials for project %s', project.name)
        return []

    if not project.search_console_property:
        logger.warning('No GSC property set for project %s', project.name)
        return []

    try:
        service = build('searchconsole', 'v1', credentials=creds)
        response = service.searchanalytics().query(
            siteUrl=project.search_console_property,
            body={
                'startDate': start_date.strftime('%Y-%m-%d'),
                'endDate': end_date.strftime('%Y-%m-%d'),
                'dimensions': ['query', 'page'],
                'rowLimit': row_limit,
                'dataState': 'final',
            },
        ).execute()

        rows = response.get('rows', [])
        logger.info(
            'GSC: fetched %d rows for project %s (%s – %s)',
            len(rows), project.name, start_date, end_date,
        )
        return rows

    except Exception as e:
        logger.error('GSC fetch error for project %s: %s', project.name, e)
        return []


def get_gsc_summary(project, days=28):
    """Возвращает суммарные клики/показы за последние N дней (для карточки проекта)."""
    from apps.analytics.models import SearchConsoleMetrics
    from django.db.models import Sum
    since = timezone.now().date() - timedelta(days=days)
    agg = SearchConsoleMetrics.objects.filter(
        project=project, date__gte=since
    ).aggregate(
        total_clicks=Sum('clicks'),
        total_impressions=Sum('impressions'),
    )
    return {
        'clicks': agg['total_clicks'] or 0,
        'impressions': agg['total_impressions'] or 0,
    }
