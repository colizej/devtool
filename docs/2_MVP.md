# AI SEO Dashboard
## Техническое задание (Technical Specification) — Редакция 2.0

- **Проект:** Локальный центр управления SEO и аналитикой сайтов
- **Тип:** Developer Tool / Internal Dashboard
- **Версия документа:** 2.0
- **Дата:** 17 марта 2026
- **Предыдущая версия:** 1_MVP.md

---

# 1. Описание проекта

Создать локальную систему (dashboard), которая объединяет данные различных SEO и аналитических сервисов и позволяет централизованно анализировать несколько сайтов.

Система должна:

- подключаться к Google Search Console
- подключаться к Google Analytics (GA4)
- анализировать sitemap
- обходить сайт (crawler)
- проверять индексацию страниц
- анализировать SEO структуру
- анализировать CTR и позиции
- формировать AI рекомендации
- выполнять `git push` после применения правок к сайту

Главная цель — **получить единый центр управления SEO проектами**.

---

# 2. Проекты для управления

На начальном этапе система управляет тремя сайтами:

| Сайт | Назначение |
|---|---|
| piecedetheatre.be | сайт с театральными пьесами, библиотекой и блогом |
| prava.be | сайт для изучения ПДД |
| clikme.ru | туристический сайт про Азию |

Каждый проект имеет: домен, путь к локальному репозиторию, sitemap URL, Google Search Console property, GA4 property.

---

# 3. Тип системы

Система создаётся как:

**локальный веб-сервис**

```
http://localhost:8000
```

Преимущества:

- безопасность (токены не покидают компьютер)
- высокая скорость
- отсутствие ограничений хостинга
- удобство разработки

В будущем возможно развёртывание на сервере.

---

# 4. Принципы разработки

## Минимализм зависимостей

Проект использует **только необходимые библиотеки**. Принцип: если задача решается стандартными средствами Django или Python stdlib — внешняя зависимость не добавляется.

**Запрещено:**
- Docker / docker-compose (заменяется нативным `venv`)
- Celery + Redis (заменяется встроенным планировщиком)
- HTMX

**Разрешено для MVP:**
```
Django                    # backend, ORM, шаблоны, admin
google-auth-oauthlib      # OAuth2 для Google API
google-api-python-client  # Search Console + GA4 API
requests                  # HTTP запросы (crawler, sitemap)
beautifulsoup4            # парсинг HTML (crawler)
python-decouple           # .env конфигурация
```

**Frontend (без npm, без сборщиков):**
```
TailwindCSS CLI standalone  # стили (standalone binary, без Node.js)
Chart.js CDN                # графики
Vanilla JavaScript          # логика
```

---

# 5. Технологический стек

## Backend

| Компонент | Решение | Примечание |
|---|---|---|
| Фреймворк | Django 5.x | |
| БД (MVP) | SQLite | встроена в Python, нет зависимостей |
| БД (prod) | PostgreSQL | при необходимости масштабирования |
| Окружение | Python venv | без Docker |
| Конфиг | python-decouple + `.env` | |
| Планировщик | django-apscheduler | легковесный, без Redis |
| HTTP клиент | requests | stdlib-близкий |
| HTML парсер | BeautifulSoup4 | |
| Google API | google-auth-oauthlib, google-api-python-client | |

## Frontend

| Компонент | Решение | Примечание |
|---|---|---|
| CSS | TailwindCSS CLI standalone | бинарник, без npm/Node.js |
| Charts | Chart.js (CDN) | |
| JS | Vanilla JS + Fetch API | |
| Icons | Heroicons (CDN) | |

### TailwindCSS — Standalone CLI (без Node.js)

Tailwind v4 предоставляет **standalone executable** — один бинарный файл для macOS/Linux/Windows.
Скачивается один раз, Node.js не требуется, npm не требуется.

**Принцип работы:**
1. Скачать бинарник → положить в папку проекта или `/usr/local/bin/`
2. Запустить `--watch` во время разработки → следит за шаблонами Django и пересобирает CSS
3. В `base.html` подключается статический `tailwind.css` — уже скомпилированный, минимальный
4. В продакшн попадает только этот файл — никаких node_modules

**Установка (macOS Apple Silicon):**
```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss-macos-arm64
mv tailwindcss-macos-arm64 tailwindcss
# Проверка:
./tailwindcss --version
```

**Установка (macOS Intel):**
```bash
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-x64
chmod +x tailwindcss-macos-x64
mv tailwindcss-macos-x64 tailwindcss
```

**Структура файлов:**
```
static/
  css/
    input.css       # исходный файл с @import "tailwindcss"
    tailwind.css    # скомпилированный (генерируется CLI, в .gitignore)
```

**`static/css/input.css`:**
```css
@import "tailwindcss";

/* Кастомные стили dashboard */
@theme {
  --color-primary: #3b82f6;
  --color-sidebar: #1e293b;
}
```

**Запуск watch во время разработки:**
```bash
./tailwindcss -i static/css/input.css -o static/css/tailwind.css --watch
```

**Сборка для продакшн (минификация):**
```bash
./tailwindcss -i static/css/input.css -o static/css/tailwind.css --minify
```

**Подключение в `base.html`:**
```html
<link href="{% static 'css/tailwind.css' %}" rel="stylesheet">
```

> Бинарник `tailwindcss` добавляется в `.gitignore`. CSS-файл `tailwind.css` — в `.gitignore` тоже (генерируется при сборке). В `requirements.txt` и `venv` ничего нового не появляется.

### Почему Vanilla JS (не HTMX, не React)

Для данного dashboard оптимален `fetch API`:
- полный контроль над запросами и состоянием
- нет конфликтов с CSRF токенами Django
- легко читать и поддерживать без build-шага
- Chart.js требует JS-контроля — при HTMX это усложняется

---

# 6. Окружение и запуск

## Установка

```bash
# 1. Python окружение
cd ~/projects
python -m venv .venv
source .venv/bin/activate

pip install django google-auth-oauthlib google-api-python-client \
            requests beautifulsoup4 python-decouple django-apscheduler

# 2. TailwindCSS standalone (macOS Apple Silicon)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss-macos-arm64 && mv tailwindcss-macos-arm64 tailwindcss

# 3. Первая сборка CSS
./tailwindcss -i static/css/input.css -o static/css/tailwind.css
```

## Структура `.env`

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

# БД (опционально, по умолчанию SQLite)
# DATABASE_URL=postgresql://user:pass@localhost:5432/seo_dashboard

# Google OAuth
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# AI Provider (MVP — бесплатный tier)
AI_PROVIDER=gemini             # gemini | openai | ollama
GEMINI_API_KEY=...
OPENAI_API_KEY=...             # опционально
OLLAMA_HOST=http://localhost:11434  # опционально

# Git
GIT_AUTO_PUSH=true             # включить автоматический git push
```

## Запуск

```bash
# Терминал 1 — Django
python manage.py migrate
python manage.py runserver

# Терминал 2 — TailwindCSS watch (только во время разработки)
./tailwindcss -i static/css/input.css -o static/css/tailwind.css --watch
```

> Два терминала — стандартная практика для Django + CSS watch. Никаких npm, никакого node_modules.

---

# 7. Архитектура системы

```
SEO Dashboard (localhost:8000)
│
├── Django Backend
│   ├── apps/projects/          # управление проектами
│   ├── apps/integrations/      # Google GSC + GA4 OAuth + API клиенты
│   ├── apps/analytics/         # хранение и обработка метрик
│   ├── apps/crawler/           # sitemap + site crawler
│   ├── apps/seo/               # SEO анализ, CTR анализ, issues
│   ├── apps/ai/                # AI рекомендации
│   ├── apps/scheduler/         # django-apscheduler задачи
│   └── apps/git_sync/          # git push после правок
│
├── templates/                  # Django HTML шаблоны
├── static/                     # CSS, JS файлы
└── logs/                       # логи API, crawler, scheduler
```

---

# 8. Структура проекта

```
seo_dashboard/
│
├── manage.py
├── .env
├── requirements.txt
│
├── dashboard/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── apps/
│   ├── projects/
│   ├── integrations/
│   ├── analytics/
│   ├── crawler/
│   ├── seo/
│   ├── ai/
│   ├── scheduler/
│   └── git_sync/
│
├── templates/
│   ├── base.html
│   ├── projects/
│   ├── analytics/
│   ├── seo/
│   └── ai/
│
├── static/
│   ├── css/
│   └── js/
│
└── logs/
    ├── api.log
    ├── crawler.log
    └── scheduler.log
```

---

# 9. Модели данных

## Project

```python
class Project(models.Model):
    PLATFORM_CHOICES = [
        ('django',    'Django'),
        ('wordpress', 'WordPress'),
        ('nextjs',    'Next.js'),
        ('nuxt',      'Nuxt.js'),
        ('shopify',   'Shopify'),
        ('hugo',      'Hugo'),
        ('jekyll',    'Jekyll'),
        ('laravel',   'Laravel'),
        ('other',     'Other'),
    ]

    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=200)           # prava.be
    slug = models.SlugField(unique=True)                # для SEO-URL
    platform = models.CharField(                        # платформа сайта
        max_length=20, choices=PLATFORM_CHOICES, default='other'
    )
    sitemap_url = models.URLField()                     # https://prava.be/sitemap.xml
    search_console_property = models.CharField(...)    # sc-domain:prava.be
    analytics_property = models.CharField(...)         # GA4 property ID
    local_repo_path = models.CharField(max_length=500) # /Users/user/projects/prava
    git_remote_url = models.CharField(max_length=500)  # git@github.com:user/prava.git
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

## SearchConsoleMetrics

```python
class SearchConsoleMetrics(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date = models.DateField()
    query = models.TextField(null=True, blank=True)   # ключевой запрос
    page = models.URLField(null=True, blank=True)     # URL страницы
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    ctr = models.FloatField(default=0)
    position = models.FloatField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['project', 'date']),
            models.Index(fields=['project', 'page']),
        ]
```

## AnalyticsMetrics

```python
class AnalyticsMetrics(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    date = models.DateField()
    users = models.IntegerField(default=0)
    sessions = models.IntegerField(default=0)
    avg_session_duration = models.FloatField(default=0)
    bounce_rate = models.FloatField(default=0)
    source_medium = models.CharField(max_length=200, null=True)
```

## SeoIssues

```python
class SeoIssue(models.Model):
    SEVERITY = [('error', 'Error'), ('warning', 'Warning'), ('notice', 'Notice')]

    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    url = models.URLField()
    issue_type = models.CharField(max_length=100)   # missing_title, low_ctr, no_h1 ...
    description = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
```

## CrawlResult

```python
class CrawlResult(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    url = models.URLField()
    status_code = models.IntegerField()
    title = models.TextField(null=True)
    meta_description = models.TextField(null=True)
    h1 = models.TextField(null=True)
    canonical = models.URLField(null=True)
    robots_index = models.BooleanField(default=True)
    load_time_ms = models.IntegerField(null=True)
    crawled_at = models.DateTimeField(auto_now_add=True)
```

## AIRecommendation

```python
class AIRecommendation(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    url = models.URLField(null=True, blank=True)
    recommendation_type = models.CharField(max_length=100)  # title, description, ctr, structure
    input_data = models.JSONField()        # данные переданные в AI
    recommendation = models.TextField()   # ответ AI
    ai_provider = models.CharField(max_length=50)  # gemini, openai, ollama
    created_at = models.DateTimeField(auto_now_add=True)
```

## GoogleOAuthToken

```python
class GoogleOAuthToken(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    scopes = models.TextField()           # список scopes через запятую
    updated_at = models.DateTimeField(auto_now=True)
```

---

# 10. Безопасность

> Система разрабатывается локально, но **архитектура безопасности закладывается с первого дня** — с расчётом на будущий деплой на сервер.

## OAuth2 Flow

1. Пользователь открывает `/auth/google/<project_id>/` → редирект на Google OAuth
2. Google возвращает `code` → обмен на `access_token` + `refresh_token`
3. Токены сохраняются в `GoogleOAuthToken` (БД, локальная)
4. Перед каждым API запросом: проверка срока `access_token`, автообновление через `refresh_token`

## Хранение секретов

- **Google Client ID/Secret** → `.env` (никогда не в git)
- **OAuth токены** → локальная БД (SQLite/PostgreSQL)
- `.gitignore` обязательно включает: `.env`, `*.sqlite3`, `logs/`, `credentials/`, `tailwindcss`, `static/css/tailwind.css`

## Django — обязательные настройки безопасности

### settings.py (dev vs prod)

```python
# Переключается через .env: DEBUG=True/False
DEBUG = config('DEBUG', cast=bool, default=False)

# Никогда не '*' в продакшн
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# CSRF
CSRF_COOKIE_SECURE = not DEBUG       # True в продакшн (только HTTPS)
CSRF_TRUSTED_ORIGINS = ['https://yourdomain.com']  # при деплое

# Session
SESSION_COOKIE_SECURE = not DEBUG    # True в продакшн
SESSION_COOKIE_HTTPONLY = True       # защита от XSS
SESSION_COOKIE_SAMESITE = 'Lax'

# Секретный ключ — всегда из .env, никогда хардкодом
SECRET_KEY = config('SECRET_KEY')

# Заголовки безопасности (активно в продакшн)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

## Аутентификация пользователя dashboard

Dashboard содержит приватные данные (токены, SEO метрики). Доступ должен быть защищён:

| Этап | Метод | Реализация |
|---|---|---|
| Локально (MVP) | Django `@login_required` | встроенная авторизация |
| Сервер (prod) | Django auth + HTTPS | nginx + Let's Encrypt |
| Сервер (опционально) | HTTP Basic Auth на уровне nginx | до регистрации пользователей |

**MVP:** создать суперпользователя при инициализации. Все views защищены `@login_required`.

```python
# Все views закрыты
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin

# Function-based:
@login_required
def dashboard(request): ...

# Class-based:
class ProjectView(LoginRequiredMixin, View): ...
```

## Защита от основных угроз (OWASP Top 10)

| Угроза | Меры |
|---|---|
| Injection (SQL) | Django ORM — нет raw SQL без параметризации |
| XSS | Django шаблон auto-escape включён, явный `\|safe` только там где нужно |
| CSRF | Django `CsrfViewMiddleware` включён, `X-CSRFToken` в fetch-запросах |
| Broken Auth | `@login_required` на всех views, `SESSION_COOKIE_SECURE` в prod |
| Sensitive Data | `.env` + `.gitignore`, логи без токенов |
| SSRF (crawler) | Crawler обходит только домены из `Project.domain`, запрещены `localhost`, `169.254.*` |
| Command Injection (git) | `commit_message` формируется системой, не из user input |

## Подготовка к серверному деплою (Phase 5+)

Эти настройки **не нужны сейчас**, но структура кода должна их поддерживать:

```
nginx                        # reverse proxy + SSL termination
gunicorn                     # WSGI сервер вместо runserver
Let's Encrypt (certbot)      # HTTPS сертификат
SECURE_HSTS_SECONDS          # HTTP Strict Transport Security
DEBUG=False + ALLOWED_HOSTS  # обязательно в prod
python manage.py collectstatic  # статика через nginx
```

**Что закладываем уже сейчас:**
- `settings.py` читает всё из `.env` — переключение local → prod меняет только `.env`
- `STATIC_ROOT` настроен (даже если сейчас не используется `collectstatic`)
- Нет хардкода URL, IP, паролей в коде
- `requirements.txt` зафиксированы версии (`==` вместо `>=`) перед деплоем

---

# 11. Интеграции

## Google Search Console API

**Библиотека:** `google-api-python-client`

Используется для:
- получение кликов, показов, CTR, позиций
- разрез по: query, page, date, country, device
- проверка индексации через URL Inspection API

**Квоты GSC:**
- 200 запросов/день на property
- ответ: до 25,000 строк за один запрос
- **Стратегия:** 1 импорт в сутки + кэш в БД

## Google Analytics GA4

**Библиотека:** `google-api-python-client` (GA4 Data API)

Используется для:
- пользователи, сессии, время на сайте
- bounce rate
- источники трафика (source/medium)
- **Стратегия:** 1 импорт в сутки + кэш в БД

---

# 12. Sitemap анализ

Система должна:

1. Скачать `sitemap.xml` через `requests`
2. Распарсить XML (включая `<sitemapindex>` — вложенные sitemaps)
3. Сохранить все URLs в БД
4. Сравнить с индексированными страницами из GSC

Проблемы которые система обнаруживает:
- страница есть в sitemap, но не индексируется
- страница индексируется, но отсутствует в sitemap
- дубликаты URL в sitemap

---

# 13. Crawler сайта

**Реализация:** `requests` + `BeautifulSoup4` (без Scrapy)

Crawler должен:
- обходить сайт начиная с главной страницы
- уважать `robots.txt`
- соблюдать задержку: **1–2 секунды** между запросами
- не обходить внешние ссылки

**Сбор данных с каждой страницы:**
- HTTP status code
- title (длина, содержание)
- meta description (длина, содержание)
- h1 (наличие, количество)
- canonical URL
- robots meta (index/noindex)
- broken links (ссылки с 4xx/5xx)
- время загрузки (в мс)

---

# 14. Проверка индексации

Через **GSC URL Inspection API**.

Статусы страниц:
- `indexed` — в индексе
- `not_indexed` — не в индексе
- `discovered_not_indexed` — обнаружена, не проиндексирована
- `excluded` — исключена (canonical, noindex и др.)

Система сравнивает: sitemap URLs ↔ индексированные URLs → генерирует `SeoIssue` для расхождений.

---

# 15. Анализ CTR

**Алгоритм обнаружения проблем:**

```
если impressions > 500
AND CTR < 1%
→ SeoIssue: severity=warning, type=low_ctr
→ отправить в AI для анализа title/description
```

```
если position < 10
AND CTR < средний CTR для данной позиции
→ SeoIssue: severity=warning, type=ctr_below_average
```

**Результат:** сохраняется как `SeoIssue` + передаётся в AI модуль по запросу.

---

# 16. SEO анализ

Проверки по каждой странице:

| Проверка | Критерий | Severity |
|---|---|---|
| Title length | &lt; 30 или &gt; 65 символов | warning |
| Title отсутствует | нет тега | error |
| Description length | &lt; 100 или &gt; 165 символов | warning |
| Description отсутствует | нет тега | warning |
| H1 отсутствует | нет H1 | error |
| Несколько H1 | более одного H1 | warning |
| Canonical отсутствует | нет canonical | notice |
| Дубли title | совпадает с другой страницей | error |
| Дубли description | совпадает с другой страницей | warning |
| Noindex | robots meta = noindex | notice |

---

# 17. AI модуль

## Принцип работы

AI используется **только для рекомендаций**. Система никогда не применяет изменения автоматически.

AI анализирует:
- SEO проблемы страниц
- предлагает варианты title
- предлагает варианты meta description
- объясняет причины низкого CTR
- рекомендует структурные улучшения

## Провайдеры AI

**Стратегия по версиям:**

| Этап | Провайдер | Стоимость |
|---|---|---|
| MVP | Google Gemini API (Free Tier) | бесплатно до лимита |
| MVP резерв | Ollama (локальный) | бесплатно, нет интернета |
| Продакшн | OpenAI GPT-4o-mini | платно, по мере роста |
| Продакшн+ | OpenAI GPT-4o | платно, для сложных задач |

**Gemini Free Tier:** 15 запросов/минуту, 1500 запросов/день — достаточно для MVP.
**Ollama:** локальная LLM (llama3, mistral) — 100% бесплатно, без интернета, чуть слабее качеством.

## Абстрактный интерфейс

```python
class AIProvider:
    def analyze(self, prompt: str) -> str:
        raise NotImplementedError

class GeminiProvider(AIProvider): ...
class OllamaProvider(AIProvider): ...
class OpenAIProvider(AIProvider): ...

# Выбор через .env: AI_PROVIDER=gemini
```

## Примеры промптов

**CTR анализ:**
```
Page: {url}
Title: {title}
Impressions: {impressions} | CTR: {ctr}% | Position: {position}
Top queries: {top_queries}

Task: Explain why CTR is low. Suggest 3 improved title variants (max 60 chars).
Language: match the site language ({language}).
```

**SEO аудит страницы:**
```
Page: {url}
Issues found: {issues_list}
Current title: {title}
Current description: {description}

Task: Provide specific recommendations to fix each issue. Be concise.
```

## Контроль стоимости

- AI вызывается **только по запросу пользователя** (кнопка "Generate AI Report")
- Батч: не более 20 страниц за один запуск
- Результаты сохраняются в `AIRecommendation` — повторные запросы для той же страницы не отправляются, если данные свежие (< 7 дней)

---

# 18. Git Sync — публикация правок

После того как пользователь применил рекомендацию AI или исправил SEO проблему вручную, система выполняет `git push` в репозиторий сайта.

## Сценарий использования

1. AI предложил новый title для страницы `/beaches-vietnam`
2. Пользователь одобрил и сохранил изменение в файле шаблона сайта
3. Dashboard выполняет: `git add → git commit → git push`
4. Изменение публикуется в репозитории

## Реализация

```python
# apps/git_sync/service.py
import subprocess

class GitSyncService:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def push(self, commit_message: str) -> dict:
        """Выполняет git add, commit, push."""
        commands = [
            ['git', 'add', '-A'],
            ['git', 'commit', '-m', commit_message],
            ['git', 'push'],
        ]
        results = []
        for cmd in commands:
            result = subprocess.run(
                cmd, cwd=self.repo_path,
                capture_output=True, text=True
            )
            results.append({
                'command': ' '.join(cmd),
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
            })
            if result.returncode != 0:
                break  # остановить при ошибке
        return results

    def status(self) -> str:
        """Возвращает git status."""
        result = subprocess.run(
            ['git', 'status', '--short'],
            cwd=self.repo_path, capture_output=True, text=True
        )
        return result.stdout
```

## Безопасность Git Sync

- `local_repo_path` из модели `Project` — только абсолютный путь, проверяется при сохранении
- `commit_message` — не принимается от пользователя как сырой ввод; формируется системой на основе типа исправления
- SSH-ключ настраивается один раз на уровне ОС — Dashboard не хранит SSH credentials
- Git push выполняется только с явного подтверждения пользователя (кнопка с confirmation dialog)

---

# 19. Планировщик задач

**Реализация:** `django-apscheduler` (без Redis и Celery)

## Расписание

| Задача | Частота | Описание |
|---|---|---|
| import_gsc_data | 1 раз в сутки | Импорт метрик GSC для всех проектов |
| import_ga4_data | 1 раз в сутки | Импорт метрик GA4 |
| run_seo_analysis | 1 раз в сутки | Анализ SEO issues по последним данным |
| check_indexation | 2 раза в неделю | URL Inspection API для приоритетных страниц |
| run_crawler | 1 раз в неделю | Полный обход каждого сайта |
| parse_sitemaps | 1 раз в неделю | Обновление URL из sitemaps |

**Настройка частоты** будет доступна на уровне проекта в Phase 2.

---

# 20. Интерфейс

## Главная страница `/`

Список проектов с карточками:

```
┌─────────────────────────────────┐
│ piecedetheatre.be               │
│ Clicks: 430  ▲ +12%             │
│ Impressions: 8,200              │
│ Issues: 3 errors, 12 warnings   │
│ [Open Project]                  │
└─────────────────────────────────┘
```

## Страница проекта `/project/<id>/`

Вкладки:

| Вкладка | Содержимое |
|---|---|
| Overview | сводка: клики, показы, CTR, позиция (7d / 30d / 90d) |
| Traffic | графики GA4: users, sessions, sources |
| Queries | топ запросы GSC с позицией и CTR |
| Pages | все страницы: clicks, impressions, CTR, status |
| SEO Issues | таблица с фильтрами по severity и типу |
| Crawler | статус последнего обхода, результаты |
| AI Report | рекомендации AI, кнопка "Generate" |
| Git Sync | статус репозитория, история push |

---

# 21. Логирование

Файлы логов в `logs/`:

| Файл | Содержимое |
|---|---|
| `logs/api.log` | все запросы к Google API (статус, время, ошибки) |
| `logs/crawler.log` | результаты crawl (URL, статус, ошибки) |
| `logs/scheduler.log` | выполнение задач планировщика |
| `logs/git.log` | git push операции |
| `logs/ai.log` | запросы к AI (провайдер, токены, ответ) |

Ротация логов: `RotatingFileHandler`, максимум 10MB на файл, 5 архивов.

---

# 22. Ограничения Google API

| API | Лимит | Стратегия |
|---|---|---|
| Search Console | 200 req/day | 1 полный импорт/сутки, остаток на URL Inspection |
| GA4 Data API | 10,000 req/day | 1 импорт/сутки |
| URL Inspection | 2,000 req/day | только приоритетные страницы |

**Кэширование:** все данные сохраняются в БД. Повторные запросы к API не делаются, если данные за текущие сутки уже есть.

---

# 23. Возможные риски

| Риск | Вероятность | Митигация |
|---|---|---|
| OAuth refresh token истёк | Высокая | автообновление через `google-auth-oauthlib` |
| GSC API quota превышена | Средняя | кэш + 1 запрос в сутки |
| Crawler блокировка (403/429) | Средняя | User-Agent, задержки, robots.txt |
| AI галлюцинации | Высокая | только рекомендации, никаких авто-изменений |
| Git push конфликт | Низкая | проверять `git status` перед push, логировать ошибку |
| Большой объём GSC данных | Средняя | пагинация при импорте (по 25,000 строк) |
| Sitemap Index (вложенные) | Средняя | рекурсивный парсер |
| Смена API Google | Низкая | монитор changelog, изоляция API клиентов в `integrations/` |

---

# 24. Этапы разработки

## Phase 0 — Фундамент (~1 неделя)

- [ ] Django проект со структурой приложений
- [ ] `.env` + `python-decouple`
- [ ] Скачать TailwindCSS standalone CLI, создать `static/css/input.css`, первая сборка `tailwind.css`
- [ ] Базовые шаблоны (`base.html`, навигация, sidebar)
- [ ] Логирование (`RotatingFileHandler`)
- [ ] Модель `Project` + Django admin

**Результат:** `localhost:8000` открывается, можно добавить проект через admin

---

## Phase 1 — GSC Core (~2–3 недели)

- [ ] Google OAuth2 flow (`/auth/google/<project_id>/`)
- [ ] Хранение токенов в `GoogleOAuthToken`
- [ ] GSC API клиент + импорт метрик (clicks, impressions, ctr, position, query, page)
- [ ] `django-apscheduler` daily job
- [ ] Dashboard: список проектов с summary
- [ ] Страница проекта → вкладка Queries

**Результат:** видны реальные данные GSC для всех 3 сайтов

---

## Phase 2 — Analytics & CTR (~2 недели)

- [ ] GA4 API клиент + импорт метрик
- [ ] CTR анализ → `SeoIssue` generation
- [ ] Chart.js: графики кликов, показов, трафика
- [ ] Date range picker (7d / 30d / 90d)
- [ ] Redis cache (опционально, если SQLite медленная)

**Результат:** графики трафика, список страниц с проблемами CTR

---

## Phase 3 — Technical SEO (~3 недели)

- [ ] Sitemap парсер (включая sitemap index)
- [ ] Crawler: `requests` + `BeautifulSoup4`, async через `asyncio`
- [ ] SEO checker: проверки title, description, h1, canonical, dups
- [ ] URL Inspection API: статусы индексации
- [ ] Сравнение: sitemap ↔ indexed ↔ crawled
- [ ] Вкладки: SEO Issues, Crawler, Pages

**Результат:** полный технический аудит в один клик

---

## Phase 4 — AI & Git Sync (~2 недели)

- [ ] Абстрактный `AIProvider` интерфейс
- [ ] Gemini Free Tier провайдер
- [ ] Ollama провайдер (резерв)
- [ ] Промпты для CTR анализа, title/description
- [ ] `AIRecommendation` модель + вкладка AI Report
- [ ] `GitSyncService`: `git add → commit → push`
- [ ] Вкладка Git Sync с историей операций

**Результат:** AI рекомендации + публикация правок через git

---

## Phase 5 — Advanced (по необходимости)

| Фича | Описание |
|---|---|
| PageSpeed Insights | Core Web Vitals: LCP, CLS, FID |
| Alerts | Telegram-бот при падении трафика/позиций |
| PDF Reports | WeasyPrint еженедельный отчёт |
| Bing Webmaster Tools | дополнительный поисковый источник |
| PostgreSQL migration | при росте объёма данных |
| OpenAI платный tier | при необходимости лучшего качества AI |
| Platform adapters | Специфичные проверки для WordPress, Next.js, Shopify (см. раздел 28) |

---

# 25. Минимальный requirements.txt

```
Django>=5.0
google-auth-oauthlib>=1.2
google-api-python-client>=2.120
requests>=2.31
beautifulsoup4>=4.12
python-decouple>=3.8
django-apscheduler>=0.6
```

> **Итого: 7 зависимостей** для полного рабочего MVP.

---

# 26. Стратегия тестирования

> Тесты — не опциональная задача «на потом». Они закладываются с Phase 0 и покрывают критические пути.

## Принцип

Тестировать **бизнес-логику и интеграции**, не Django-фреймворк. Не гнаться за 100% coverage — покрывать то, что болезненно падает в проде.

## Используемые инструменты

```
Django TestCase       # встроен в Django, база для всех тестов
unittest.mock         # мокирование Google API (входит в stdlib Python)
```

> Никаких дополнительных зависимостей — `pytest` не нужен для данного масштаба.

## Типы тестов и приоритеты

### Unit-тесты (высокий приоритет)

Тестируют изолированную логику без внешних вызовов:

| Модуль | Что тестировать |
|---|---|
| `seo/` | CTR алгоритм (impressions > 500, ctr < 1%), severity grades |
| `seo/` | SEO checker: title length, description length, дубли |
| `crawler/` | парсинг HTML: title, h1, canonical, meta из фиксированного HTML |
| `crawler/` | sitemap parser: вложенные sitemaps, дубли URL |
| `git_sync/` | формирование commit message, валидация repo_path |
| `ai/` | маршрутизация провайдера по `AI_PROVIDER` из .env |

### Integration-тесты (средний приоритет)

Тестируют взаимодействие компонентов с мокированными внешними API:

```python
# Пример: тест импорта GSC с моком API
from unittest.mock import patch, MagicMock
from django.test import TestCase
from apps.integrations.gsc import import_gsc_data
from apps.projects.models import Project

class GSCImportTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name='Test', domain='test.be',
            search_console_property='sc-domain:test.be'
        )

    @patch('apps.integrations.gsc.build')  # мок google API client
    def test_import_saves_metrics(self, mock_build):
        mock_build.return_value.searchanalytics().query().execute.return_value = {
            'rows': [{'keys': ['test query', 'https://test.be/page'], 'clicks': 10,
                      'impressions': 500, 'ctr': 0.02, 'position': 5.0}]
        }
        import_gsc_data(self.project)
        from apps.analytics.models import SearchConsoleMetrics
        self.assertEqual(SearchConsoleMetrics.objects.count(), 1)
        self.assertEqual(SearchConsoleMetrics.objects.first().clicks, 10)
```

### View-тесты (средний приоритет)

```python
from django.test import TestCase, Client
from django.contrib.auth.models import User

class DashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser('admin', '', 'password')

    def test_dashboard_requires_login(self):
        response = self.client.get('/')
        self.assertRedirects(response, '/accounts/login/?next=/')

    def test_dashboard_logged_in(self):
        self.client.login(username='admin', password='password')
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
```

## Структура тестов

```
apps/
  projects/
    tests/
      test_models.py
      test_views.py
  integrations/
    tests/
      test_gsc.py       # с моком API
      test_ga4.py
  seo/
    tests/
      test_ctr.py
      test_checker.py
  crawler/
    tests/
      test_sitemap.py
      test_crawler.py
  git_sync/
    tests/
      test_service.py
```

## Запуск тестов

```bash
# Все тесты
python manage.py test

# Конкретное приложение
python manage.py test apps.seo

# С подробным выводом
python manage.py test --verbosity=2
```

## Когда писать тесты

| Фаза | Что тестировать обязательно |
|---|---|
| Phase 0 | тест login_required на всех views |
| Phase 1 | GSC импорт (мок API), модель Project валидация |
| Phase 2 | CTR алгоритм, GA4 импорт (мок) |
| Phase 3 | SEO checker логика, sitemap parser, crawler HTML парсинг |
| Phase 4 | AI провайдер routing, git_sync commit message формирование |

---

# 27. SEO для самого Dashboard (при деплое на сервер)

> Сейчас не актуально. Но структура кода должна поддерживать это с первого дня.

## Когда это становится важным

Если dashboard будет развёрнут как публичный SaaS-сервис или landing page для привлечения клиентов — SEO будет критичен.

## Что закладываем сейчас (без усилий)

### Структура URL — человекочитаемая

```python
# urls.py — уже при разработке делать читаемые URL
urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('project/<slug:slug>/', views.project_detail, name='project-detail'),
    path('project/<slug:slug>/seo/', views.seo_issues, name='seo-issues'),
]
```

Модель `Project` должна иметь поле `slug`:
```python
from django.utils.text import slugify
slug = models.SlugField(unique=True)  # добавить в модель Project
```

### Meta-теги в base.html (шаблонизация)

```html
<!-- templates/base.html -->
<head>
  <title>{% block title %}AI SEO Dashboard{% endblock %}</title>
  <meta name="description" content="{% block description %}Локальный центр управления SEO проектами{% endblock %}">
  <meta name="robots" content="{% block robots %}noindex, nofollow{% endblock %}">
  <!-- Локально и в приватном деплое — noindex ОБЯЗАТЕЛЕН -->
</head>
```

### robots.txt — с первого дня

```python
# urls.py
from django.views.generic import TemplateView
path('robots.txt', TemplateView.as_view(
    template_name='robots.txt', content_type='text/plain'
)),
```

```
# templates/robots.txt
# Локальная / приватная версия — закрыть всё
User-agent: *
Disallow: /
```

> При публичном деплое `robots.txt` корректируется под нужды продвижения.

### Что добавить при публичном деплое (Phase 5+)

| Элемент | Описание |
|---|---|
| `sitemap.xml` | `django.contrib.sitemaps` — карта публичных страниц |
| Open Graph теги | для шаринга в соцсетях |
| structured data | `schema.org/SoftwareApplication` |
| canonical теги | исключить дубли URL |
| HTTPS | обязателен для позиций в поиске |
| PageSpeed | Core Web Vitals влияют на ранжирование |
| `lang` атрибут | `<html lang="ru">` — важно для геотаргетинга |

---

# 28. Мультиплатформенность (архитектурная закладка)

## Ключевой принцип

**Анализируемые сайты могут быть на любой платформе.** Сам dashboard — Django.
Бо́льшая часть системы уже платформонезависима: GSC/GA4 API, crawler, sitemap-парсер, CTR-анализ, AI — работают одинаково для любого сайта.
Платформа имеет значение только для **специфичных проверок** (Phase 5+).

## Что платформонезависимо (уже сейчас)

| Модуль | Зависит от платформы? |
|---|---|
| Google Search Console | ❌ работает для любого домена |
| Google Analytics GA4 | ❌ |
| Crawler (HTTP + BeautifulSoup4) | ❌ анализирует HTML-ответ |
| Sitemap парсер | ❌ стандарт XML |
| CTR / SEO анализ | ❌ алгоритм по данным GSC |
| AI рекомендации | ❌ |
| Git Sync | ❌ стандартный git |

## Что закладываем сейчас (без усилий)

### 1. Поле `platform` в модели Project

Уже добавлено в раздел 9. Даёт возможность в будущем:
- фильтровать проекты по платформе
- подключать платформо-специфичные адаптеры
- показывать релевантные советы в AI промптах

### 2. Абстрактный адаптер платформы (заготовка)

```python
# apps/projects/adapters.py
class PlatformAdapter:
    """Базовый адаптер. Работает для любого сайта."""

    def get_platform_checks(self, crawl_result) -> list:
        """Возвращает список платформо-специфичных проверок."""
        return []  # по умолчанию — ничего дополнительного

    def get_ai_platform_hint(self) -> str:
        """Подсказка для AI промпта о платформе."""
        return ""


class WordPressAdapter(PlatformAdapter):
    def get_platform_checks(self, crawl_result) -> list:
        checks = []
        # Проверить наличие Yoast/RankMath meta тегов
        # Проверить /wp-json/ доступность
        # Проверить /wp-content/ структуру
        return checks

    def get_ai_platform_hint(self) -> str:
        return "Site is built on WordPress. Consider Yoast SEO recommendations."


class NextJsAdapter(PlatformAdapter):
    def get_ai_platform_hint(self) -> str:
        return "Site is built on Next.js. Check for SSR/SSG meta tag rendering."


# Реестр адаптеров
PLATFORM_ADAPTERS = {
    'wordpress': WordPressAdapter,
    'nextjs':    NextJsAdapter,
    'django':    PlatformAdapter,   # базовый
    'other':     PlatformAdapter,
}

def get_adapter(platform: str) -> PlatformAdapter:
    cls = PLATFORM_ADAPTERS.get(platform, PlatformAdapter)
    return cls()
```

> Адаптер вызывается в SEO analyzer и передаётся в AI модуль.
> В MVP все адаптеры возвращают пустой результат — код работает, ничего не ломается.

## Специфика платформ (реализация в Phase 5+)

| Платформа | Специфичные проверки |
|---|---|
| **WordPress** | Yoast/RankMath meta, `/wp-json/` API, `xmlrpc.php` отключён (безопасность), WP-Cron настройка |
| **Next.js / Nuxt** | SSR рендеринг meta-тегов (проверка без JS), `_next/static` кэш, `next-sitemap` конфиг |
| **Shopify** | `schema.org/Product`, canonical для вариантов товара, Liquid-шаблоны |
| **Hugo / Jekyll** | структура `public/` при git push, front matter поля (title, description) |
| **Laravel** | `php artisan sitemap`, Laravel SEO пакеты |

## Вывод

Сейчас: **одно поле + пустой адаптер** — 15 минут работы, ноль overhead.
Потом: каждая платформа получает свой адаптер независимо, не трогая остальной код.
Архитектура готова к расширению без рефакторинга.

---

*Версия 2.2 — 17.03.2026*
*v2.1: безопасность (Django settings, OWASP, @login_required, деплой), тестирование (unit/integration/view), SEO dashboard (slug, robots.txt, meta-шаблоны).*
*v2.2: мультиплатформенность — поле `platform` в модели Project, абстрактный `PlatformAdapter`, таблица специфичных проверок (WordPress, Next.js, Shopify, Hugo, Laravel). Архитектура платформонезависима с Phase 0, адаптеры подключаются в Phase 5+.*
