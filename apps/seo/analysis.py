"""
CTR Analysis Service.
Compares real CTR with industry benchmark by position.

NOTE: All analyze_* functions preserve existing `status` and `note` fields
so that manually reviewed/fixed issues are never reset on re-analysis.
New issues are created, outdated issues are deleted, existing ones are updated
with fresh metrics only — status/note remain untouched.
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Avg

logger = logging.getLogger("seo")

_BENCH = {1: 0.28, 2: 0.15, 3: 0.11, 4: 0.08, 5: 0.06,
          6: 0.05, 7: 0.04, 8: 0.03, 9: 0.025, 10: 0.02}


def _upsert_issues(project, issue_type, new_issues):
    """
    Sync issues of a given type for a project without losing status/note.

    - Existing issues (matched by query+page) → update metrics, keep status/note
    - New issues not seen before → create
    - Old issues no longer in current data → delete
    """
    from .models import SeoIssue

    # Build lookup key → new issue data
    new_map = {(i.query, i.page): i for i in new_issues}

    existing = {
        (obj.query, obj.page): obj
        for obj in SeoIssue.objects.filter(project=project, issue_type=issue_type)
    }

    to_create = []
    to_update = []
    update_fields = ['priority', 'clicks', 'impressions', 'ctr', 'position', 'potential_clicks']

    for key, new in new_map.items():
        if key in existing:
            obj = existing[key]
            for f in update_fields:
                setattr(obj, f, getattr(new, f))
            to_update.append(obj)
        else:
            to_create.append(new)

    # Delete issues that disappeared from current data
    stale_keys = set(existing.keys()) - set(new_map.keys())
    if stale_keys:
        stale_qs = [(q, p) for q, p in stale_keys]
        for query, page in stale_qs:
            SeoIssue.objects.filter(
                project=project, issue_type=issue_type, query=query, page=page
            ).delete()

    if to_create:
        SeoIssue.objects.bulk_create(to_create)
    if to_update:
        SeoIssue.objects.bulk_update(to_update, update_fields)

    return len(new_map)


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

    count = _upsert_issues(project, "low_ctr", issues)
    logger.info("CTR analysis for %s: %d issues", project.name, count)
    return count


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

    count = _upsert_issues(project, "low_position", issues)
    logger.info("Low-position analysis for %s: %d issues", project.name, count)
    return count


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

    count = _upsert_issues(project, "no_clicks", issues)
    logger.info("No-clicks analysis for %s: %d issues", project.name, count)
    return count


def run_full_analysis(project, days=30):
    """Запускает все три типа анализа и возвращает общее количество проблем."""
    total = 0
    total += analyze_ctr(project, days)
    total += analyze_low_position(project, days)
    total += analyze_no_clicks(project, days)
    logger.info("Full SEO analysis for %s: %d total issues", project.name, total)
    return total
