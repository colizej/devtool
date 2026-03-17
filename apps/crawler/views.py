import threading
import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from apps.projects.models import Project
from .models import CrawlSession, CrawlResult

logger = logging.getLogger('crawler')


def _run_crawl(project, session):
    """Запускается в отдельном потоке."""
    from .engine import crawl_site
    try:
        count = crawl_site(project, session)
        session.status = 'done'
        session.pages_crawled = count
        session.pages_found = CrawlResult.objects.filter(session=session).count()
    except Exception as e:
        logger.error('Crawl failed for %s: %s', project.name, e)
        session.status = 'error'
        session.error_message = str(e)[:500]
    finally:
        session.finished_at = timezone.now()
        session.save(update_fields=['status', 'pages_crawled', 'pages_found', 'finished_at', 'error_message'])


@login_required
def crawl_start(request, project_id):
    """Запуск краулера для проекта."""
    if request.method != 'POST':
        return redirect('projects:dashboard')
    project = get_object_or_404(Project, pk=project_id)

    if CrawlSession.objects.filter(project=project, status='running').exists():
        messages.warning(request, f'Краулер для «{project.name}» уже запущен.')
        return redirect(f'/project/{project.slug}/?tab=crawler')

    session = CrawlSession.objects.create(project=project)
    thread = threading.Thread(target=_run_crawl, args=(project, session), daemon=True)
    thread.start()

    messages.success(request, f'Краулер запущен для «{project.name}». Обновите страницу через минуту.')
    return redirect(f'/project/{project.slug}/?tab=crawler')
