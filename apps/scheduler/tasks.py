import logging
from datetime import timedelta, date
from django.utils import timezone
from apps.projects.models import Project
from apps.analytics.models import SearchConsoleMetrics
from apps.integrations.gsc import fetch_gsc_data

logger = logging.getLogger('scheduler')


def import_gsc_for_project(project, days_back=3):
    """
    Импортирует данные GSC для одного проекта за последние days_back дней.
    Использует update_or_create чтобы не дублировать записи.
    """
    end_date = timezone.now().date() - timedelta(days=1)  # вчера (данные финальные)
    start_date = end_date - timedelta(days=days_back - 1)

    rows = fetch_gsc_data(project, start_date, end_date)
    if not rows:
        return 0

    created_count = 0
    for row in rows:
        keys = row.get('keys', [])
        query = keys[0] if len(keys) > 0 else ''
        page = keys[1] if len(keys) > 1 else ''

        _, created = SearchConsoleMetrics.objects.update_or_create(
            project=project,
            date=end_date,
            query=query,
            page=page,
            defaults={
                'clicks': int(row.get('clicks', 0)),
                'impressions': int(row.get('impressions', 0)),
                'ctr': float(row.get('ctr', 0.0)),
                'position': float(row.get('position', 0.0)),
            },
        )
        if created:
            created_count += 1

    logger.info('GSC import: %d new rows for project %s', created_count, project.name)
    return created_count


def import_gsc_all_projects():
    """Ежедневная задача: импорт GSC данных для всех активных проектов."""
    projects = Project.objects.filter(
        is_active=True,
        search_console_property__isnull=False,
    ).exclude(search_console_property='')

    total = 0
    for project in projects:
        try:
            count = import_gsc_for_project(project)
            total += count
        except Exception as e:
            logger.error('GSC import failed for project %s: %s', project.name, e)

    logger.info('GSC daily import complete: %d total new rows for %d projects', total, projects.count())
    return total


def import_ga4_for_project(project, days_back=3):
    """
    Импортирует данные GA4 для одного проекта за последние days_back дней.
    Разбивает по дате + каналу (sessionDefaultChannelGroup).
    """
    from apps.integrations.ga4 import fetch_ga4_data
    from apps.analytics.models import GA4Metrics

    if not project.analytics_property:
        logger.info('GA4 skip %s — no property_id', project.name)
        return 0

    rows = fetch_ga4_data(project, days_back=days_back)
    if not rows:
        return 0

    count = 0
    for row in rows:
        _, created = GA4Metrics.objects.update_or_create(
            project=project,
            date=row['date'],
            channel=row['channel'],
            defaults={
                'sessions':              row['sessions'],
                'users':                 row['users'],
                'new_users':             row['new_users'],
                'pageviews':             row['pageviews'],
                'bounce_rate':           row['bounce_rate'],
                'avg_session_duration':  row['avg_session_duration'],
            },
        )
        if created:
            count += 1

    logger.info('GA4 import: %d new rows for project %s', count, project.name)
    return count


def import_ga4_all_projects():
    """Ежедневная задача: импорт GA4 данных для всех активных проектов."""
    projects = Project.objects.filter(
        is_active=True,
        analytics_property__isnull=False,
    ).exclude(analytics_property='')

    total = 0
    for project in projects:
        try:
            total += import_ga4_for_project(project)
        except Exception as e:
            logger.error('GA4 import failed for project %s: %s', project.name, e)

    logger.info('GA4 daily import complete: %d new rows for %d projects', total, projects.count())
    return total
