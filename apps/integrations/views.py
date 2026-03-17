import os
import json
import logging
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from google_auth_oauthlib.flow import Flow
from apps.projects.models import Project
from .models import GoogleOAuthToken

logger = logging.getLogger('integrations')

SCOPES = [
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/analytics.readonly',
]

# Разрешаем HTTP для локальной разработки
if settings.DEBUG:
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


def _build_flow(request, project_id):
    """Создаёт Flow объект для OAuth2."""
    flow = Flow.from_client_config(
        {
            'web': {
                'client_id': settings.GOOGLE_CLIENT_ID,
                'client_secret': settings.GOOGLE_CLIENT_SECRET,
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [request.build_absolute_uri(
                    reverse('integrations:google_callback')
                )],
            }
        },
        scopes=SCOPES,
    )
    flow.redirect_uri = request.build_absolute_uri(
        reverse('integrations:google_callback')
    )
    return flow


@login_required
def google_auth(request, project_id):
    """Шаг 1: перенаправляем пользователя на Google для авторизации."""
    project = get_object_or_404(Project, pk=project_id)
    flow = _build_flow(request, project_id)
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent',
    )
    request.session['oauth_state'] = state
    request.session['oauth_project_id'] = project_id
    # Сохраняем code_verifier для PKCE (google-auth-oauthlib >= 1.0)
    if hasattr(flow, 'code_verifier') and flow.code_verifier:
        request.session['oauth_code_verifier'] = flow.code_verifier
    logger.info('OAuth2 flow started for project %s', project.name)
    return redirect(auth_url)


@login_required
def google_callback(request):
    """Шаг 2: Google перенаправляет сюда с кодом авторизации."""
    state = request.session.get('oauth_state')
    project_id = request.session.get('oauth_project_id')

    if not state or not project_id:
        messages.error(request, 'Сессия авторизации устарела. Попробуйте снова.')
        return redirect('projects:dashboard')

    if 'error' in request.GET:
        messages.error(request, f'Ошибка авторизации: {request.GET["error"]}')
        return redirect('projects:dashboard')

    project = get_object_or_404(Project, pk=project_id)
    flow = _build_flow(request, project_id)
    # Восстанавливаем code_verifier для PKCE (google-auth-oauthlib >= 1.0)
    code_verifier = request.session.pop('oauth_code_verifier', None)
    if code_verifier:
        flow.code_verifier = code_verifier
    flow.fetch_token(authorization_response=request.build_absolute_uri())

    creds = flow.credentials
    expiry = timezone.now() + timedelta(seconds=3600)
    if creds.expiry:
        from django.utils.timezone import make_aware
        import datetime
        if isinstance(creds.expiry, datetime.datetime):
            expiry = make_aware(creds.expiry) if creds.expiry.tzinfo is None else creds.expiry

    GoogleOAuthToken.objects.update_or_create(
        project=project,
        defaults={
            'access_token': creds.token,
            'refresh_token': creds.refresh_token or '',
            'token_expiry': expiry,
            'scopes': ' '.join(creds.scopes or SCOPES),
        },
    )

    # Очищаем session
    del request.session['oauth_state']
    del request.session['oauth_project_id']

    logger.info('OAuth2 token saved for project %s', project.name)
    messages.success(request, f'Гугл-аккаунт успешно подключён к {project.name}')
    return redirect('projects:detail', slug=project.slug)


@login_required
def gsc_import_now(request, project_id):
    """Ручной запуск импорта GSC данных для проекта."""
    if request.method != 'POST':
        return redirect('projects:dashboard')
    project = get_object_or_404(Project, pk=project_id)
    from apps.scheduler.tasks import import_gsc_for_project
    try:
        count = import_gsc_for_project(project, days_back=30)
        messages.success(request, f'Импорт завершён: загружено {count} новых записей для «{project.name}»')
    except Exception as e:
        logger.error('Manual GSC import failed for %s: %s', project.name, e)
        messages.error(request, f'Ошибка импорта: {e}')
    return redirect('projects:detail', slug=project.slug)


@login_required
def run_seo_analysis(request, project_id):
    """Запуск CTR анализа для проекта."""
    if request.method != 'POST':
        return redirect('projects:dashboard')
    project = get_object_or_404(Project, pk=project_id)
    from apps.seo.analysis import run_full_analysis
    try:
        count = run_full_analysis(project, days=30)
        messages.success(request, f'Анализ завершён: найдено {count} SEO проблем для «{project.name}»')
    except Exception as e:
        logger.error('SEO analysis failed for %s: %s', project.name, e)
        messages.error(request, f'Ошибка анализа: {e}')
    return redirect(f'/project/{project.slug}/?tab=seo')


@login_required
def update_issue_status(request, issue_id):
    """AJAX endpoint: обновляет статус и заметку SeoIssue."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    from apps.seo.models import SeoIssue
    issue = get_object_or_404(SeoIssue, pk=issue_id)

    valid_statuses = {s for s, _ in SeoIssue.STATUS}
    new_status = request.POST.get('status', '').strip()
    note = request.POST.get('note', '').strip()

    if new_status and new_status not in valid_statuses:
        return JsonResponse({'error': 'Invalid status'}, status=400)

    if new_status:
        issue.status = new_status
    if 'note' in request.POST:
        issue.note = note
    issue.save(update_fields=['status', 'note', 'updated_at'])

    return JsonResponse({
        'ok': True,
        'status': issue.status,
        'status_label': issue.get_status_display(),
    })


@login_required
def ga4_import_now(request, project_id):
    """Ручной импорт GA4 данных для проекта."""
    if request.method != 'POST':
        return redirect('projects:dashboard')
    project = get_object_or_404(Project, pk=project_id)
    from apps.scheduler.tasks import import_ga4_for_project
    try:
        count = import_ga4_for_project(project, days_back=90)
        messages.success(request, f'GA4: импортировано {count} записей для «{project.name}»')
    except Exception as e:
        err_str = str(e)
        logger.error('GA4 import failed for %s: %s', project.name, err_str)
        if 'ACCESS_TOKEN_SCOPE_INSUFFICIENT' in err_str or 'insufficient authentication scopes' in err_str.lower():
            messages.warning(
                request,
                'Токен не имеет доступа к GA4. Нажмите «Переподключить Google» чтобы обновить разрешения.'
            )
            # Удаляем токен чтобы показ кнопки re-auth
            project.google_token.delete()
        else:
            messages.error(request, f'Ошибка импорта GA4: {err_str}')
    return redirect(f'/project/{project.slug}/?tab=traffic')
