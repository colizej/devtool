# AI SEO Dashboard
## Техническое задание (Technical Specification)

- **Проект:** Локальный центр управления SEO и аналитикой сайтов
- **Тип:** Developer Tool / Internal Dashboard
- **Версия документа:** 1.0
- **Дата:** 2026

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
- анализировать репозитории Git
- формировать AI рекомендации

Главная цель — **получить единый центр управления SEO проектами**.

---

# 2. Проекты для управления

На начальном этапе система управляет тремя сайтами:

| Сайт | Назначение |
|-----|-----|
| piecedetheatre.be | сайт с театральными пьесами, библиотекой и блогом |
| prava.be | сайт для изучения ПДД |
| clikme.ru | туристический сайт про Азию |

---

# 3. Тип системы

Система создаётся как:

**локальный веб-сервис**

http://localhost:8000


Преимущества:

- безопасность (токены не покидают компьютер)
- высокая скорость
- отсутствие ограничений хостинга
- удобство разработки

В будущем возможно развёртывание на сервере.

---

# 4. Архитектура системы

## Общая схема

```
SEO Dashboard
│
├── Django Backend
│
├── Integrations
│ ├── Google Search Console
│ ├── Google Analytics
│
├── Crawlers
│ ├── sitemap parser
│ ├── site crawler
│
├── Analysis
│ ├── SEO analyzer
│ ├── CTR analyzer
│
├── AI Engine
│
└── Scheduler
```

---

# 5. Технологический стек

## Backend


Python
Django
PostgreSQL (или SQLite для MVP)


## Frontend


TailwindCSS
Vanilla JavaScript
Chart.js


### Почему не HTMX

HTMX может конфликтовать с Django CSRF и сложнее масштабируется при сложной логике интерфейса.

Для данного проекта лучше использовать:


vanilla JS + fetch API


Это проще контролировать и масштабировать.

---

# 6. Структура проекта


seo_dashboard/

manage.py

dashboard/
settings.py
urls.py

apps/

projects/
integrations/
analytics/
crawler/
seo/
ai/
scheduler/

templates/
static/

logs/


---

# 7. Модели данных

## Project


name
domain
repository_url
sitemap_url
search_console_property
analytics_property
server_path
created_at


---

## SearchConsoleMetrics


project
date
clicks
impressions
ctr
position


---

## AnalyticsMetrics


project
date
users
sessions
avg_time
bounce_rate


---

## SeoIssues


project
url
issue_type
description
severity
created_at


---

## CrawlResult


project
url
status_code
title
meta_description
h1
canonical
load_time


---

# 8. Интеграции

## Google Search Console API

Используется для:

- кликов
- показов
- CTR
- позиций
- запросов
- страниц

### Возможности


получение статистики
анализ CTR
анализ позиций
проверка индексации


---

## Google Analytics GA4

Используется для:


трафик
поведение пользователей
время на странице
bounce rate
источники трафика


---

# 9. Sitemap анализ

Система должна:


скачать sitemap.xml
распарсить URL
сравнить с индексированными страницами


Возможные проблемы:

- страница есть в sitemap но не индексируется
- страница отсутствует в sitemap
- дубликаты

---

# 10. Crawler сайта

Crawler должен:


обходить сайт
собирать SEO данные


Проверки:

- title
- meta description
- h1
- canonical
- robots
- broken links
- статус страницы

---

# 11. Проверка индексации

Проверка выполняется через:


Google Search Console URL Inspection API


Система должна определить:


indexed
not indexed
discovered but not indexed
excluded


---

# 12. Анализ CTR

Алгоритм:


если impressions > 500
и CTR < 1%

→ страница имеет плохой title
→ нужна оптимизация


Результат:


SEO recommendation


---

# 13. SEO анализ

Проверяются:


длина title
длина description
наличие h1
дубли meta
отсутствие canonical


---

# 14. Анализ репозитория

Система должна анализировать Git репозиторий сайта.

Проверки:


наличие meta
schema.org
структура HTML
robots.txt
sitemap


---

# 15. AI модуль

ИИ используется для:


анализ SEO
предложение title
предложение description
анализ CTR
анализ структуры сайта


Пример результата:


Page: /beaches-vietnam

Impressions: 4800
CTR: 0.4%

Recommendation:
Improve title and description
Add FAQ section


---

# 16. Планировщик задач

Все проверки выполняются автоматически.

Частота:


1 раз в день


В будущем частота может быть:


раз в час
раз в неделю


Для каждого проекта частота может настраиваться отдельно.

Реализация:


cron
или
Celery + Redis


Для MVP достаточно cron.

---

# 17. Интерфейс

## Главная страница


Projects


Пример:


piecedetheatre.be
Clicks: 430
Trend: +12%

prava.be
Clicks: 120
Trend: +5%

clikme.ru
Clicks: 820
Trend: +34%


---

## Страница проекта

Разделы:


overview
traffic
queries
pages
seo issues
crawler
ai report


---

# 18. Логирование

Система должна сохранять:


ошибки API
результаты анализа
crawler отчёты


Логи хранятся в:


/logs


---

# 19. Безопасность

Важно:

- хранить OAuth токены безопасно
- не публиковать dashboard в интернет без защиты
- ограничить доступ к Google API ключам

---

# 20. Ограничения Google API

Google API имеет ограничения:


quota limits
rate limits


Рекомендуется:


кешировать данные
не запрашивать API слишком часто


---

# 21. Этапы разработки

## Этап 1 (MVP)


создать Django проект
модель Project
подключение Search Console
главный dashboard


---

## Этап 2


Google Analytics
графики трафика
анализ CTR


---

## Этап 3


sitemap анализ
crawler
SEO проверки


---

## Этап 4


AI рекомендации
SEO отчёты


---

# 22. Возможные риски

### API ограничения

Google может ограничить запросы.

---

### изменение API

Google периодически меняет API.

---

### crawler нагрузка

Нужно ограничить скорость обхода сайта.

---

### ложные SEO рекомендации

AI не должен автоматически изменять сайт.

Система должна **только давать рекомендации**.

---

# 23. Расширения и перспективы

В будущем можно добавить:

## новые интеграции


PageSpeed Insights
Google Ads
Bing Webmaster Tools
Ahrefs API
Cloudflare API


---

## дополнительные анализаторы


Core Web Vitals
schema.org validator
competitor analysis
backlink analysis


---

## расширение AI

ИИ сможет:


писать статьи
анализировать конкурентов
оптимизировать структуру сайта
генерировать FAQ


---

## автоматизация разработки

Можно добавить:


GitHub integration
Pull Request suggestions
SEO fixes recommendations


---

## SaaS версия

Если система станет стабильной:

можно сделать SaaS сервис:


SEO dashboard platform


---

# 24. Рекомендации

Не стоит сразу реализовывать весь функционал.

Лучший путь:


MVP → тестирование → расширение


Начать стоит с:


Projects
Search Console
Traffic dashboard


Это позволит быстро получить рабочую систему.

После этого можно постепенно добавлять:


crawler
SEO анализ
AI


---

# 25. Заключение

Проект представляет собой **локальную SEO аналитическую платформу**, объединяющую данные различных сервисов и предоставляющую централизованный анализ сайтов.

Система должна:

- экономить время анализа
- выявлять SEO проблемы
- давать рекомендации
- объединять данные из разных источников

В перспективе проект может перерасти в полноценную SEO платформу.