"""
Site Crawler — httpx + BeautifulSoup4.
Синхронный краулер с rate limiting и respect robots.txt.
"""
import logging
import re
import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx
from bs4 import BeautifulSoup
from django.utils import timezone

logger = logging.getLogger('crawler')

HEADERS = {
    'User-Agent': 'SEODashboardBot/1.0 (+https://github.com/colizej/devtool)',
    'Accept-Language': 'ru,en;q=0.9',
}
REQUEST_TIMEOUT = 15
CRAWL_DELAY = 1.0        # секунд между запросами
MAX_PAGES = 500          # лимит страниц за сессию


def _get_robots(base_url: str) -> RobotFileParser:
    """Fetch robots.txt via httpx (respects verify=False) and parse manually.
    Falls back to allow-all if the file can't be fetched."""
    rp = RobotFileParser()
    robots_url = urljoin(base_url, '/robots.txt')
    rp.set_url(robots_url)
    try:
        resp = httpx.get(robots_url, headers=HEADERS, timeout=10,
                         follow_redirects=True, verify=False)
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
        elif resp.status_code in (401, 403):
            rp.disallow_all = True
        else:
            # 404 or other non-blocking code → allow all
            rp.allow_all = True
    except Exception:
        # Network error → allow all (we own the site)
        rp.allow_all = True
    return rp


def _is_same_domain(url: str, base: str) -> bool:
    return urlparse(url).netloc == urlparse(base).netloc


def _normalize_url(url: str) -> str:
    """Убираем fragment и trailing slash различия."""
    p = urlparse(url)
    path = p.path.rstrip('/') or '/'
    return p._replace(fragment='', query='', path=path).geturl()


def _extract_page_data(url: str, html: str, base_url: str) -> dict:
    """Парсим HTML и возвращаем SEO-данные страницы."""
    soup = BeautifulSoup(html, 'lxml')

    # Title
    title_tag = soup.find('title')
    title = title_tag.get_text(strip=True) if title_tag else ''

    # Meta description
    desc_tag = soup.find('meta', attrs={'name': re.compile(r'^description$', re.I)})
    meta_description = desc_tag.get('content', '').strip() if desc_tag else ''

    # H1
    h1_tags = soup.find_all('h1')
    h1 = h1_tags[0].get_text(strip=True) if h1_tags else ''
    h1_count = len(h1_tags)

    # Canonical
    canonical_tag = soup.find('link', rel='canonical')
    canonical = canonical_tag.get('href', '').strip() if canonical_tag else ''
    if canonical:
        canonical = urljoin(url, canonical)

    # Images без alt
    images_missing_alt = sum(
        1 for img in soup.find_all('img')
        if not img.get('alt', '').strip()
    )

    # Internal links — собираем вместе с anchor text для отслеживания битых ссылок
    internal_links = {}  # href_norm -> anchor_text (первый встреченный)
    for a in soup.find_all('a', href=True):
        href = urljoin(url, a['href'])
        href_norm = _normalize_url(href)
        if _is_same_domain(href_norm, base_url) and href_norm.startswith('http'):
            if href_norm not in internal_links:
                internal_links[href_norm] = a.get_text(strip=True)[:512]

    # Word count (text body)
    for tag in soup(['script', 'style', 'nav', 'footer', 'header']):
        tag.decompose()
    word_count = len(soup.get_text(separator=' ').split())

    return {
        'title': title[:512],
        'meta_description': meta_description[:512],
        'h1': h1[:512],
        'h1_count': h1_count,
        'canonical': canonical[:2048],
        'images_missing_alt': images_missing_alt,
        'internal_links': internal_links,  # dict: url -> anchor
        'word_count': word_count,
    }


def _check_seo_issues(data: dict, url: str) -> dict:
    """Проверяем SEO и возвращаем флаги."""
    title = data['title']
    desc = data['meta_description']
    canonical = data['canonical']
    url_norm = _normalize_url(url)
    canonical_norm = _normalize_url(canonical) if canonical else ''

    return {
        'issue_title_missing':  not title,
        'issue_title_short':    0 < len(title) < 30,
        'issue_title_long':     len(title) > 65,
        'issue_desc_missing':   not desc,
        'issue_desc_short':     0 < len(desc) < 70,
        'issue_desc_long':      len(desc) > 165,
        'issue_h1_missing':     data['h1_count'] == 0,
        'issue_h1_multiple':    data['h1_count'] > 1,
        'issue_canonical_diff': bool(canonical_norm and canonical_norm != url_norm),
    }


def crawl_site(project, session) -> int:
    """
    Краулит сайт проекта. Возвращает количество проползённых страниц.
    Сохраняет результаты в CrawlResult и BrokenLink.
    """
    from apps.crawler.models import CrawlResult, BrokenLink

    # Normalize domain: strip any existing scheme so we always build a clean URL
    domain = project.domain
    if '://' in domain:
        domain = domain.split('://', 1)[1]
    domain = domain.rstrip('/')
    base_url = f'https://{domain}'
    robots = _get_robots(base_url)
    # Уважаем Crawl-delay из robots.txt — берём максимум из нашей настройки и директивы
    robots_delay = robots.crawl_delay('*') or robots.crawl_delay('SEODashboardBot')
    effective_delay = max(CRAWL_DELAY, float(robots_delay)) if robots_delay else CRAWL_DELAY
    if effective_delay > CRAWL_DELAY:
        logger.info('robots.txt Crawl-delay: %.1fs (our default: %.1fs) — using %.1fs',
                    robots_delay, CRAWL_DELAY, effective_delay)

    visited = set()
    queue = [_normalize_url(base_url + '/')]
    count = 0
    # source_map: broken_url -> list of (found_on, anchor_text, status_code)
    link_sources: dict[str, list[tuple[str, str, int | None]]] = {}

    with httpx.Client(headers=HEADERS, timeout=REQUEST_TIMEOUT,
                      follow_redirects=True, verify=False) as client:
        while queue and count < MAX_PAGES:
            url = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            # Respect robots.txt (check against '*' wildcard — standard for most sites)
            if not robots.can_fetch('*', url):
                logger.debug('robots.txt blocked: %s', url)
                continue

            # Только HTML страницы
            parsed = urlparse(url)
            if any(parsed.path.lower().endswith(ext) for ext in
                   ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg',
                    '.pdf', '.zip', '.css', '.js', '.xml', '.ico')):
                continue

            start = time.time()
            status_code = None
            page_data = {}
            issues = {}
            is_broken = False

            try:
                resp = client.get(url)
                status_code = resp.status_code
                load_time_ms = int((time.time() - start) * 1000)

                if status_code >= 400:
                    is_broken = True
                elif 'text/html' in resp.headers.get('content-type', ''):
                    page_data = _extract_page_data(url, resp.text, base_url)
                    issues = _check_seo_issues(page_data, url)
                    # Добавляем новые ссылки в очередь, запоминаем источник
                    for link, anchor in page_data.get('internal_links', {}).items():
                        if link not in visited and link not in queue:
                            queue.append(link)
                        # Запоминаем кто ссылается на этот URL
                        link_sources.setdefault(link, []).append((url, anchor, None))
            except httpx.TimeoutException:
                status_code = None
                load_time_ms = REQUEST_TIMEOUT * 1000
                is_broken = True
                logger.warning('Timeout: %s', url)
                # Обновляем status_code в записях link_sources для этого URL
                if url in link_sources:
                    link_sources[url] = [(s, a, None) for s, a, _ in link_sources[url]]
            except Exception as e:
                logger.error('Crawl error %s: %s', url, e)
                time.sleep(effective_delay)  # задержка даже при ошибке
                continue

            # Обновляем финальный status_code в link_sources
            if is_broken and url in link_sources:
                link_sources[url] = [(s, a, status_code) for s, a, _ in link_sources[url]]

            CrawlResult.objects.update_or_create(
                session=session,
                url=url,
                defaults={
                    'project': project,
                    'status_code': status_code,
                    'title': page_data.get('title', ''),
                    'meta_description': page_data.get('meta_description', ''),
                    'h1': page_data.get('h1', ''),
                    'canonical': page_data.get('canonical', ''),
                    'load_time_ms': load_time_ms if status_code else None,
                    'word_count': page_data.get('word_count', 0),
                    'images_missing_alt': page_data.get('images_missing_alt', 0),
                    'internal_links': len(page_data.get('internal_links', {})),
                    'issue_broken': is_broken,
                    **issues,
                },
            )
            count += 1

            # Обновляем прогресс сессии каждые 10 страниц
            if count % 10 == 0:
                session.pages_crawled = count
                session.pages_found = len(visited) + len(queue)
                session.save(update_fields=['pages_crawled', 'pages_found'])

            time.sleep(effective_delay)

    # Сохраняем битые ссылки: только те URL которые оказались broken
    broken_results = set(
        CrawlResult.objects.filter(session=session, issue_broken=True)
        .values_list('url', flat=True)
    )
    broken_objs = []
    for broken_url, sources in link_sources.items():
        if broken_url in broken_results:
            seen = set()
            for found_on, anchor, code in sources:
                key = (broken_url, found_on)
                if key not in seen:
                    seen.add(key)
                    broken_objs.append(BrokenLink(
                        session=session,
                        broken_url=broken_url,
                        found_on=found_on,
                        status_code=code,
                        anchor_text=anchor,
                    ))
    if broken_objs:
        BrokenLink.objects.bulk_create(broken_objs, ignore_conflicts=True)
        logger.info('Saved %d broken links for session %d', len(broken_objs), session.pk)

    return count
