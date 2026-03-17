Markdown Preview EnhancedMarkdown Preview EnhancedMarkdown Preview Enhanced
# Roadmap — AI SEO Dashboard

**Дата:** 17 марта 2026
**Подход:** итеративная разработка, каждый этап — рабочий продукт

---

## Обзор этапов

```
Phase 0  │ Фундамент              │ ~1 неделя
Phase 1  │ MVP Core               │ ~2-3 недели
Phase 2  │ Analytics & Charts     │ ~2 недели
Phase 3  │ Technical SEO          │ ~3 недели
Phase 4  │ AI & Reports           │ ~2 недели
Phase 5  │ Advanced Features      │ ongoing
```

---

## Phase 0 — Фундамент ✅ ЗАВЕРШЕНО (17.03.2026)

> Цель: настроить окружение так, чтобы никогда не возвращаться к этому вопросу

### Задачи

- [x] Создать Django проект со структурой приложений (`projects`, `integrations`, `analytics`, `crawler`, `seo`, `ai`, `scheduler`, `git_sync`)
- [x] Настроить `.env` + `python-decouple` для секретов и токенов
- [x] Базовый `settings.py` (dev / prod разделение)
- [x] Скачать TailwindCSS standalone CLI v4.2.1, создать `static/css/input.css`, первая сборка `tailwind.css`
- [x] Базовые шаблоны: `base.html`, `navbar`, `sidebar`
- [x] Логирование: `RotatingFileHandler` → `logs/` папка
- [x] Модель `Project` + Django admin

### Дополнительно сделано

- [x] `Makefile` с командами: `make dev`, `make watch`, `make css`, `make kill`, `make test` и др.
- [x] `.gitignore`, `.env.example`, `requirements.txt`
- [x] `robots.txt` view (закрыт для индексации)
- [x] `@login_required` на всех views с первого дня
- [x] Страница логина с оформлением TailwindCSS
- [x] Страница проектов (`dashboard.html`) + страница проекта (`detail.html`)
- [x] Суперпользователь `admin` создан

### Результат фазы

`http://127.0.0.1:8001/` — открывается dashboard с навигацией и аутентификацией
`http://127.0.0.1:8001/admin/` — Django admin с моделью Project

---

## Phase 1 — MVP Core (Search Console) ✅ ЗАВЕРШЕНО (17.03.2026)

> Цель: видеть реальные данные GSC для 3 сайтов в одном месте

### Задачи

**Модели**
- [x] Модель `Project` (name, domain, sitemap_url, search_console_property)
- [x] Модель `SearchConsoleMetrics` (с полями `query` и `page`)
- [x] Django admin для управления проектами

**Google OAuth2**
- [x] Настройка Google Cloud Project `seo-dashboard` + API credentials
- [x] Реализация OAuth2 flow через `google-auth-oauthlib` с поддержкой PKCE
- [x] Хранение `refresh_token` в БД (`GoogleOAuthToken` модель)
- [x] Автообновление access token при истечении

**Search Console Integration**
- [x] Клиент GSC API — `apps/integrations/gsc.py`
- [x] Импорт данных: клики, показы, CTR, позиция (за последние 90 дней)
- [x] Импорт по разрезу: query + page + date — 1519 строк для piecedetheatre.be
- [x] Ручной импорт кнопкой «↻ Импортировать» + ежедневный scheduler

**Scheduler**
- [x] `django-apscheduler` для daily jobs (06:00)
- [x] Job: ежедневный импорт GSC данных для каждого проекта
- [x] Логирование успеха/ошибки каждого job

**Dashboard UI**
- [x] Главная страница: список проектов с real-time summary (клики, показы за 28 дней)
- [x] Страница проекта → вкладка Overview: график кликов/показов (Chart.js)
- [x] Страница проекта → вкладка Queries: топ-50 запросов с CTR и позицией
- [x] Страница проекта → вкладка Страницы: топ-50 страниц
- [x] Фильтр по периоду: 7д / 30д / 90д

### Дополнительно сделано
- [x] Django 5.1.7 → 6.0.3 (совместимость с Python 3.14)
- [x] Исправлен `InsecureTransportError` через `OAUTHLIB_INSECURE_TRANSPORT` в DEBUG
- [x] Уведомления (notifications) с кнопкой ✕

### Результат фазы

Работающий dashboard с реальными данными GSC. Импортировано 1519 строк для piecedetheatre.be.

---

## Phase 2 — Analytics & CTR Analysis ✅ ЗАВЕРШЕНО (17.03.2026)

### Задачи

**CTR Анализ** ✅
- [x] Алгоритм `analyze_ctr()`: CTR < 50% от industry benchmark по позиции → флаг
- [x] Алгоритм `analyze_low_position()`: запросы на позициях 4–20, близко к ТОП-3
- [x] Алгоритм `analyze_no_clicks()`: страницы с показами (≥5) и 0 кликов
- [x] Функция `run_full_analysis()` — запускает все три анализа
- [x] Модель `SeoIssue` с полями: issue_type, priority, status, note, query, page, ctr, position, potential_clicks
- [x] Статусы задач: Новая / Важно / В работе / Исправлено / Игнорировать
- [x] Вкладка SEO Issues: таблица с фильтрами по типу проблемы
- [x] Действия: открыть страницу сайта, сменить статус (AJAX), добавить заметку
- [x] 162 проблемы обнаружено для piecedetheatre.be (17.03.2026)

**Google Analytics GA4** ✅
- [x] Модель `GA4Metrics` (sessions, users, new_users, pageviews, bounce_rate, channel)
- [x] Разрешение GA4 Data API в Google Cloud Console
- [x] GA4 Data API клиент (`apps/integrations/ga4.py`)
- [x] Импорт: sessions, users, pageviews, bounce_rate по каналам
- [x] Вкладка Traffic на странице проекта (Summary cards + Chart.js + таблица каналов)
- [x] Scheduler job (ежедневно в 06:15)
- [x] OAuth с двумя scope: `webmasters.readonly` + `analytics.readonly`
- [x] 235 записей GA4 для piecedetheatre.be (80 дней, 5 каналов, 5640 сессий)

**Визуализация** 🔄
- [x] Chart.js line chart для GSC трафика (клики + показы)
- [x] Date range picker (7д / 30д / 90д)
- [ ] Bar chart для топ запросов
- [ ] GA4 + GSC на одном графике

**Кэширование** ⬜
- [ ] Cache для API ответов (TTL: 12 часов)
- [ ] Cache invalidation при ручном re-import
- [ ] Импорт: sessions, users, source/medium
- [ ] Вкладка Traffic на странице проекта

**CTR Анализ**
- [ ] Алгоритм: impressions > 500 AND CTR < 1% → флаг "needs optimization"
- [ ] Модель `SeoIssues` для хранения рекомендаций
- [ ] Вкладка CTR Issues: список страниц требующих внимания
- [ ] Сортировка по: потенциальный выигрыш (impressions × средний CTR - текущий CTR)

**Визуализация**
- [ ] Chart.js: line chart для трафика (GSC + GA4 на одном графике)
- [ ] Chart.js: bar chart для топ запросов
- [ ] Date range picker (7d / 30d / 90d)

**Кэширование**
- [ ] Redis cache для API ответов (TTL: 12 часов)
- [ ] Cache invalidation при ручном re-import

### Результат фазы

Видно: откуда трафик, какие страницы плохо работают, трендовые графики

---

## Phase 3 — Technical SEO 🔄 В РАБОТЕ

> Цель: автоматический аудит технического состояния сайтов

### Задачи

**Sitemap Parser**
- [ ] Скачать и распарсить `sitemap.xml` (включая `sitemap index`)
- [ ] Поддержка вложенных sitemaps (рекурсивный парсер)
- [ ] Модель `SitemapUrl` (url, lastmod, priority, changefreq)
- [ ] Сравнить URLs sitemap с проиндексированными страницами из GSC

**Site Crawler**
- [ ] Crawler на `httpx` + `BeautifulSoup4` (или `scrapy` для сложных сайтов)
- [ ] Rate limiting: задержка 1-2 сек между запросами, respect `robots.txt`
- [ ] Модель `CrawlResult` (status_code, title, meta_description, h1, canonical, load_time)
- [ ] Асинхронный crawl через `asyncio` + `httpx`
- [ ] Обнаружение broken links (4xx, 5xx)

**SEO Checker**
- [ ] Проверки: title length (50-60), description length (150-160), H1 presence, canonical
- [ ] Дубли title/description между страницами
- [ ] Missing alt на изображениях
- [ ] Severity grades: Error / Warning / Notice

**Indexation Checker**
- [ ] URL Inspection API (GSC)
- [ ] Статусы: indexed / not indexed / excluded / discovered
- [ ] Приоритизация: страницы в sitemap, но не индексированы — критическая ошибка

**UI**
- [ ] Вкладка SEO Issues: таблица с фильтрами по severity и типу
- [ ] Вкладка Crawler: прогресс-бар crawl + результаты
- [ ] Вкладка Pages: comparison sitemap vs indexed vs crawled

### Результат фазы

Полный технический аудит сайта в один клик

---

## Phase 4 — AI & Reports

> Цель: умные рекомендации и экспорт

### Задачи

**AI Engine**
- [ ] Выбор провайдера: OpenAI GPT-4o (рекомендован) или Ollama (локальный, бесплатный)
- [ ] Абстрактный интерфейс `AIProvider` (легко менять провайдера)
- [ ] Промпты для: анализ CTR, предложение title/description, анализ SEO issues
- [ ] Батч-обработка: не более 20 страниц за раз (контроль стоимости)
- [ ] Хранение результатов в `AIRecommendation` модели

**Примеры промптов:**
```
Prompt: SEO Title Optimizer
---
Page URL: {url}
Current title: {title}
Impressions: {impressions}
CTR: {ctr}%
Position: {position}
Top queries: {queries}

Suggest 3 improved title variants (max 60 chars) that would increase CTR.
Explain why CTR is low.
```

**Reports**
- [ ] PDF отчёт по проекту (weekly summary) через `weasyprint` или `reportlab`
- [ ] CSV экспорт: queries, pages, issues
- [ ] Еженедельный email отчёт (опционально, через django email)

**UI**
- [ ] Вкладка AI Report: список рекомендаций по страницам
- [ ] Кнопка "Generate AI Report" (on-demand)
- [ ] История рекомендаций с датами

### Результат фазы

Dashboard генерирует actionable рекомендации, exportable reports

---

## Phase 5 — Advanced Features (Ongoing)

> Расширения по необходимости

| Фича | Описание |
|---|---|
| **🎨 Редизайн под цвета лого** | Извлечь доминирующие цвета из `static/logo.png` (Pillow), обновить CSS-переменные в `tailwind.css` и `base.html` — сайдбар, акцентные цвета, кнопки |
| PageSpeed Insights API | Core Web Vitals: LCP, CLS, FID для каждой страницы |
| Alerts система | Telegram-бот или email при резком падении трафика/позиций |
| Bing Webmaster Tools | Дополнительный источник поисковых данных |
| Ahrefs API | Backlinks, Domain Rating |
| Multi-user | Аутентификация для команды, роли admin/viewer |
| Server deploy | Docker Compose на VPS, nginx, HTTPS |
| Mobile-responsive UI | Адаптивная версия dashboard |
| Competitive analysis | Сравнение позиций с конкурентами |

---

## Стек финальной версии

```
Backend:        Django 5.x
Database:       SQLite (МВП) → PostgreSQL (при необходимости)
Scheduler:      django-apscheduler
Frontend:       TailwindCSS CLI standalone + Vanilla JS + Chart.js
AI:             Gemini Free Tier (МВП) → Ollama (резерв) → OpenAI (продакшн)
Crawler:        requests + BeautifulSoup4
Secrets:        python-decouple + .env
Okружение:      Python venv (без Docker)
```

---

## Ключевые принципы разработки

1. **Каждая фаза — рабочий продукт.** Не начинать Phase 2, если Phase 1 не работает стабильно
2. **Data first.** Сначала данные корректно собираются и хранятся — потом UI
3. **AI — последний слой.** AI работает только на уже собранных данных
4. **Не спешить с UI.** Django admin достаточен для Phase 0-1
5. **Логировать всё.** Особенно API вызовы — GSC ошибки неочевидны

---

## Первые 3 шага прямо сейчас

```bash
# 1. Создать виртуальное окружение и Django проект
python -m venv .venv && source .venv/bin/activate
pip install django python-decouple django-apscheduler
django-admin startproject dashboard .

# 2. Скачать TailwindCSS standalone (macOS Apple Silicon)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-macos-arm64
chmod +x tailwindcss-macos-arm64 && mv tailwindcss-macos-arm64 tailwindcss

# 3. Создать первое приложение и модель Project
python manage.py startapp projects
```

---

*Roadmap создан: 17.03.2026*
