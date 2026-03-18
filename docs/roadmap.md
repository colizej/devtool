Markdown Preview EnhancedMarkdown Preview EnhancedMarkdown Preview Enhanced
# Roadmap — AI SEO Dashboard

**Дата:** 17 марта 2026 → обновлено 18 марта 2026
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

## Phase 3 — Technical SEO ✅ ЗАВЕРШЕНО (17.03.2026)

> Цель: автоматический аудит технического состояния сайтов

### Задачи

**Site Crawler** ✅
- [x] Crawler на `httpx` + `BeautifulSoup4`
- [x] Rate limiting: задержка 1 сек между запросами, respect `robots.txt`
- [x] Модель `CrawlSession` (статус, прогресс, время выполнения)
- [x] Модель `CrawlResult` (status_code, title, meta_description, h1, canonical, load_time, word_count, images_missing_alt, internal_links)
- [x] Обнаружение broken links (4xx/5xx)
- [x] Лимит 500 страниц за сессию

**SEO Checker** ✅
- [x] Title: отсутствует / короткий (<30) / длинный (>65)
- [x] Meta description: отсутствует / короткий (<70) / длинный (>165)
- [x] H1: отсутствует / несколько H1
- [x] Canonical ≠ URL
- [x] Images без alt атрибута
- [x] Severity grades: Error / Warning / OK

**UI** ✅
- [x] Вкладка Crawler: кнопка запуска, статус сессии, прогресс
- [x] Таблица результатов с фильтрами по severity (Все / Ошибки / Предупреждения / ОК)
- [x] Summary cards: всего страниц / предупреждений / без ошибок
- [x] Запуск в фоновом потоке (не блокирует UI)

**Баги исправлены** ✅
- [x] **robots.txt SSL-блокировка (Python 3.14):** `RobotFileParser.read()` использует `urllib` внутри, который падает с `SSL: CERTIFICATE_VERIFY_FAILED` → entries остаются пустыми → `can_fetch()` возвращает `False` для всех URL. Исправлено: `_get_robots()` теперь использует `httpx` (с `verify=False`) + `rp.parse()` напрямую
- [x] **domain с протоколом в БД:** поле `domain` для clikme.ru хранилось как `https://clikme.ru`, engine делал `f'https://{domain}'` → невалидный URL. Исправлено: нормализация в `crawl_site()` + исправлено в БД
- [x] **Django DB в background thread:** `close_old_connections()` добавлен в `_run_crawl()` — Django не передаёт DB-соединения в новые потоки

### Результат фазы

Полный технический аудит сайта в один клик — до 500 страниц, 11 SEO-проверок.
Протестировано на piecedetheatre.be и clikme.ru.

---

## Phase 4 — AI & Reports ✅ ЗАВЕРШЕНО (17–18.03.2026)

> Цель: умные рекомендации на основе собранных данных

### Задачи

**AI Engine** ✅
- [x] Провайдер: **Gemini 2.5 Flash** (`google-genai` SDK)
- [x] Модель `AIRequest` (project, url, rec_type, prompt, response, created_at)
- [x] `apps/ai/` — отдельное приложение
- [x] Промпты: Title / Description / H1 оптимизация на основе GSC-данных + краулера

**UI (AI-модал)** ✅
- [x] Кнопка "AI Fix" в таблице краулера (для страниц с проблемами)
- [x] Модал с вкладками: Title / Description / H1 — генерирует 3 варианта каждого
- [x] Список SEO-проблем страницы отображается в заголовке модала (цветные бейджи)
- [x] Кнопки "Открыть страницу" и "Открыть Admin" в подвале модала
- [x] Копирование результата: `textarea` с `onclick="this.select()"`
- [x] Пауза авто-рефреша краулера при открытом модале

**SEO Issues — улучшения** ✅
- [x] **Upsert-логика** (`_upsert_issues()`): при повторном анализе сохраняются `status` и `note` — не затираются
- [x] Статусы: Новая / Важно / В работе / Исправлено / Игнорировать
- [x] Заметки к проблемам (inline через fetch без перезагрузки страницы)

**UI/UX — общие улучшения** ✅
- [x] Все emoji заменены на SVG Heroicons
- [x] Сортируемые заголовки таблицы краулера (все 6 колонок, SVG-иконки ↕/↑/↓)
- [x] Тултип с полным текстом ячейки (кликабельный, Cmd+C)
- [x] `admin_url` у проекта — прямая ссылка в Django-admin сайта

### Результат фазы

AI-модал работает на реальных данных. 194 страницы piecedetheatre.be проанализированы, кнопка "AI Fix" доступна для страниц с проблемами.

---

## Phase 4.1 — Crawler UX ✅ ЗАВЕРШЕНО (18.03.2026)

> Багфиксы и улучшения краулера после реального использования

- [x] **Кнопка "Остановить"** (красная) — сбрасывает зависший/активный сеанс краулера
- [x] **`crawl_reset` view + URL** — `POST /crawler/reset/<session_id>/`
- [x] **Race condition fix** — `refresh_from_db()` перед финальным save, чтобы не перезаписать `error` → `done`
- [x] **Умный polling** вместо авто-рефреша по таймеру:
  - каждые 5с запрашивает `/crawler/status/<id>/` (JSON endpoint)
  - обновляет счётчик пройденных страниц в реальном времени
  - перезагружает страницу только когда краулер завершился **И** модал закрыт
  - при открытом AI-модале показывает "Краулер завершён — обновится после закрытия"
- [x] Flash-сообщение при запуске убрало лишний текст "обновите через минуту"

---

## Phase 5 — Advanced Features (Ongoing)

> Расширения по необходимости

### Вкладка AI Report (в разработке)
- [ ] Сводный AI-отчёт по всему проекту (не по одной странице)
- [ ] Экспорт отчёта (PDF / CSV / Markdown)
- [ ] Еженедельный scheduler job: автогенерация отчёта

### Вкладка Git Sync (в разработке)
- [ ] Синхронизация с git-репозиторием сайта (`local_repo_path`)
- [ ] Авто-применение AI-правок через git commit

### Краулер — улучшения
- [ ] Поиск по таблице результатов (поле в UI есть, логика не написана)
- [ ] Сравнение двух сессий краулера (было / стало)
- [ ] Пагинация или виртуальный скролл при 500+ страницах

### SEO Issues — улучшения
- [ ] Bulk-смена статуса (выбрать несколько → отметить как fixed)
- [ ] Экспорт в CSV

### Прочее
| Фича | Описание |
|---|---|
| **🎨 Редизайн под цвета лого** | Извлечь доминирующие цвета из `static/logo.png` (Pillow), обновить CSS-переменные |
| PageSpeed Insights API | Core Web Vitals: LCP, CLS, FID для каждой страницы |
| Alerts система | Telegram-бот или email при резком падении трафика/позиций |
| Multi-user | Аутентификация для команды, роли admin/viewer |
| Server deploy | Docker Compose на VPS, nginx, HTTPS, PostgreSQL, Celery + Redis |
| Mobile-responsive UI | Адаптивная версия dashboard |

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
