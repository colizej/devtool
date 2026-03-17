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

    # Internal links
    internal_links = set()
    for a in soup.find_all('a', href=True):
        href = urljoin(url, a['href'])
        href_norm = _normalize_url(href)
        if _is_same_domain(href_norm, base_url) and href_norm.startswith('http'):
            internal_links.add(href_norm)

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
        'internal_links': list(internal_links),
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
    Сохраняет результаты в CrawlResult.
    """
    from apps.crawler.models import CrawlResult

    # Normalize domain: strip any existing scheme so we always build a clean URL
    domain = project.domain
    if '://' in domain:
        domain = domain.split('://', 1)[1]
    domain = domain.rstrip('/')
    base_url = f'https://{domain}'
    robots = _get_robots(base_url)

    visited = set()
    queue = [_normalize_url(base_url + '/')]
    count = 0

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
                    # Добавляем новые ссылки в очередь
                    for link in page_data.get('internal_links', []):
                        if link not in visited and link not in queue:
                            queue.append(link)
            except httpx.TimeoutException:
                status_code = None
                load_time_ms = REQUEST_TIMEOUT * 1000
                is_broken = True
                logger.warning('Timeout: %s', url)
            except Exception as e:
                logger.error('Crawl error %s: %s', url, e)
                continue

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
                    'internal_links': len(page_data.get('internal_links', [])),
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

            time.sleep(CRAWL_DELAY)

    return count
