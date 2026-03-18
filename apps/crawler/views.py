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
    from django.db import close_old_connections
    close_old_connections()  # Django DB connections don't transfer to new threads
    from .engine import crawl_site
    new_status = 'error'
    error_msg = ''
    count = 0
    found = 0
    try:
        count = crawl_site(project, session)
        new_status = 'done'
        found = CrawlResult.objects.filter(session=session).count()
    except Exception as e:
        logger.error('Crawl failed for %s: %s', project.name, e)
        error_msg = str(e)[:500]
    finally:
        # Не перезаписываем статус если сессия была сброшена вручную
        session.refresh_from_db(fields=['status'])
        if session.status == 'running':
            session.status = new_status
            session.pages_crawled = count
            session.pages_found = found
            session.finished_at = timezone.now()
            session.error_message = error_msg
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


@login_required
def crawl_reset(request, session_id):
    """Сброс зависшей/активной сессии краулера."""
    if request.method != 'POST':
        return redirect('projects:dashboard')
    session = get_object_or_404(CrawlSession, pk=session_id)
    project = session.project
    session.status = 'error'
    session.error_message = 'Остановлен вручную'
    session.finished_at = timezone.now()
    session.save(update_fields=['status', 'error_message', 'finished_at'])
    messages.info(request, 'Сессия краулера остановлена.')
    return redirect(f'/project/{project.slug}/?tab=crawler')
