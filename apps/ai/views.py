import json
import logging
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
from apps.projects.models import Project
from .gemini import GeminiClient, AIError
from .models import AIRecommendation

logger = logging.getLogger('django')


@login_required
@require_POST
def ai_fix(request, project_id):
    """
    AJAX endpoint.
    Body JSON: {"url": "...", "rec_type": "title|description|h1|ctr_analysis"}
    Returns: {"ok": true, "result": {...}, "rec_id": 123}
    """
    project = get_object_or_404(Project, pk=project_id)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    url      = body.get('url', '').strip()
    rec_type = body.get('rec_type', '').strip()

    if not url or rec_type not in ('title', 'description', 'h1', 'ctr_analysis'):
        return JsonResponse({'ok': False, 'error': 'Missing url or rec_type'}, status=400)

    # Собираем контекст: краулер + GSC
    from apps.crawler.models import CrawlResult, CrawlSession
    from apps.analytics.models import SearchConsoleMetrics

    crawl_data = {}
    session = CrawlSession.objects.filter(project=project, status='done').order_by('-finished_at').first()
    if session:
        result = CrawlResult.objects.filter(session=session, url=url).first()
        if result:
            crawl_data = {
                'title':            result.title,
                'meta_description': result.meta_description,
                'h1':               result.h1,
                'word_count':       result.word_count,
            }

    # Топ-5 запросов GSC для этой страницы
    gsc_queries = list(
        SearchConsoleMetrics.objects
        .filter(project=project, page=url)
        .order_by('-impressions')
        .values('query', 'clicks', 'impressions', 'ctr', 'position')[:5]
    )

    input_data = {
        'url':         url,
        'rec_type':    rec_type,
        'crawl':       crawl_data,
        'gsc_queries': gsc_queries,
        'lang':        _detect_lang(project.domain),
    }

    try:
        client = GeminiClient()
        result_data, tokens = client.generate(rec_type, input_data)
    except AIError as e:
        logger.error('AI fix failed for %s: %s', url, e)
        return JsonResponse({'ok': False, 'error': str(e)}, status=502)

    rec = AIRecommendation.objects.create(
        project=project,
        url=url,
        rec_type=rec_type,
        input_data=input_data,
        result=result_data,
        tokens_used=tokens,
    )

    return JsonResponse({'ok': True, 'result': result_data, 'rec_id': rec.pk})


def _detect_lang(domain: str) -> str:
    """Определяем язык сайта по домену для промпта."""
    if domain.endswith('.ru'):
        return 'Russian'
    if domain.endswith('.be') or domain.endswith('.fr'):
        return 'French'
    return 'English'
