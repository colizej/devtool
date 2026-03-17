"""
CTR Analysis Service.
Compares real CTR with industry benchmark by position.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg

logger = logging.getLogger("seo")

_BENCH = {1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.06,
          6: 0.05, 7: 0.04, 8: 0.03, 9: 0.025, 10: 0.02}


def _expected_ctr(position):
    pos = int(round(position))
    if pos <= 0:
        return 0.02
    if pos > 10:
        return 0.01
    return _BENCH.get(pos, 0.01)


def analyze_ctr(project, days=30):
    from apps.analytics.models import SearchConsoleMetrics
    from .models import SeoIssue

    since = timezone.now().date() - timedelta(days=days)

    query_stats = (
        SearchConsoleMetrics.objects
        .filter(project=project, date__gte=since)
        .values("query", "page")
        .annotate(
            total_clicks=Sum("clicks"),
            total_impressions=Sum("impressions"),
            avg_ctr=Avg("ctr"),
            avg_position=Avg("position"),
        )
        .filter(total_impressions__gte=10)
        .order_by("-total_impressions")
    )

    if not query_stats.exists():
        logger.info("CTR analysis: no data for %s", project.name)
        return 0

    SeoIssue.objects.filter(project=project, issue_type="low_ctr").delete()

    issues = []
    for row in query_stats:
        ctr = row["avg_ctr"] or 0.0
        impressions = row["total_impressions"]
        clicks = row["total_clicks"] or 0
        position = row["avg_position"] or 10.0
        expected = _expected_ctr(position)

        if ctr < expected * 0.5:
            potential = max(int(impressions * (expected - ctr)), 0)
            if potential >= 1:
                if potential >= 20:
                    priority = "high"
                elif potential >= 5:
                    priority = "medium"
                else:
                    priority = "low"
                issues.append(SeoIssue(
                    project=project,
                    issue_type="low_ctr",
                    priority=priority,
                    query=row["query"] or "",
                    page=row["page"] or "",
                    clicks=clicks,
                    impressions=impressions,
                    ctr=round(ctr * 100, 2),
                    position=round(position, 1),
                    potential_clicks=potential,
                ))

    SeoIssue.objects.bulk_create(issues)
    logger.info("CTR analysis for %s: %d issues", project.name, len(issues))
    return len(issues)


def analyze_low_position(project, days=30):
    """
    Находит запросы на позициях 4–20 с потенциалом выйти в ТОП-3.
    Такие запросы близко к первой странице, но теряют большинство кликов.
    """
    from apps.analytics.models import SearchConsoleMetrics
    from .models import SeoIssue

    since = timezone.now().date() - timedelta(days=days)

    query_stats = (
        SearchConsoleMetrics.objects
        .filter(project=project, date__gte=since)
        .values("query", "page")
        .annotate(
            total_clicks=Sum("clicks"),
            total_impressions=Sum("impressions"),
            avg_ctr=Avg("ctr"),
            avg_position=Avg("position"),
        )
        .filter(total_impressions__gte=5, avg_position__gte=4, avg_position__lte=20)
        .order_by("avg_position")
    )

    if not query_stats.exists():
        return 0

    SeoIssue.objects.filter(project=project, issue_type="low_position").delete()

    issues = []
    for row in query_stats:
        position = row["avg_position"] or 10.0
        impressions = row["total_impressions"]
        ctr = row["avg_ctr"] or 0.0

        # Потенциал = разница между CTR на текущей и потенциальной позиции (ТОП-3)
        target_ctr = _expected_ctr(max(1, int(position) - 3))
        potential = max(int(impressions * (target_ctr - ctr)), 0)

        if potential >= 1:
            if position <= 5:
                priority = "high"   # позиция 4-5: почти в топ-3
            elif position <= 10:
                priority = "medium" # позиция 6-10: первая страница
            else:
                priority = "low"    # позиция 11-20: вторая страница

            issues.append(SeoIssue(
                project=project,
                issue_type="low_position",
                priority=priority,
                query=row["query"] or "",
                page=row["page"] or "",
                clicks=row["total_clicks"] or 0,
                impressions=impressions,
                ctr=round(ctr * 100, 2),
                position=round(position, 1),
                potential_clicks=potential,
            ))

    SeoIssue.objects.bulk_create(issues)
    logger.info("Low-position analysis for %s: %d issues", project.name, len(issues))
    return len(issues)


def analyze_no_clicks(project, days=30):
    """
    Находит страницы/запросы с показами, но нулевым CTR (0 кликов).
    Такие запросы мелькают в выдаче, но тайтл/description не привлекают.
    """
    from apps.analytics.models import SearchConsoleMetrics
    from .models import SeoIssue

    since = timezone.now().date() - timedelta(days=days)

    query_stats = (
        SearchConsoleMetrics.objects
        .filter(project=project, date__gte=since)
        .values("query", "page")
        .annotate(
            total_clicks=Sum("clicks"),
            total_impressions=Sum("impressions"),
            avg_ctr=Avg("ctr"),
            avg_position=Avg("position"),
        )
        .filter(total_impressions__gte=5, total_clicks=0)
        .order_by("-total_impressions")
    )

    if not query_stats.exists():
        return 0

    SeoIssue.objects.filter(project=project, issue_type="no_clicks").delete()

    issues = []
    for row in query_stats:
        impressions = row["total_impressions"]
        position = row["avg_position"] or 10.0
        expected = _expected_ctr(position)
        potential = max(int(impressions * expected), 0)

        if impressions >= 20:
            priority = "high"
        elif impressions >= 10:
            priority = "medium"
        else:
            priority = "low"

        issues.append(SeoIssue(
            project=project,
            issue_type="no_clicks",
            priority=priority,
            query=row["query"] or "",
            page=row["page"] or "",
            clicks=0,
            impressions=impressions,
            ctr=0.0,
            position=round(position, 1),
            potential_clicks=potential,
        ))

    SeoIssue.objects.bulk_create(issues)
    logger.info("No-clicks analysis for %s: %d issues", project.name, len(issues))
    return len(issues)


def run_full_analysis(project, days=30):
    """Запускает все три типа анализа и возвращает общее количество проблем."""
    total = 0
    total += analyze_ctr(project, days)
    total += analyze_low_position(project, days)
    total += analyze_no_clicks(project, days)
    logger.info("Full SEO analysis for %s: %d total issues", project.name, total)
    return total
