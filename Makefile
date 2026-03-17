# ============================================================
# AI SEO Dashboard — Makefile
# ============================================================
# Использование: make <команда>
# ============================================================

VENV        = .venv
PYTHON      = $(VENV)/bin/python
PIP         = $(VENV)/bin/pip
MANAGE      = $(PYTHON) manage.py
TAILWIND    = ./tailwindcss
CSS_IN      = static/css/input.css
CSS_OUT     = static/css/tailwind.css
PORT        = 8001

.PHONY: help dev css watch install migrate migrations shell superuser test \
        collectstatic clean logs kill

# ─── Помощь ──────────────────────────────────────────────────────────────────
help:
	@echo ""
	@echo "  AI SEO Dashboard — доступные команды:"
	@echo ""
	@echo "  Разработка:"
	@echo "    make dev          — запустить Django сервер на порту $(PORT)"
	@echo "    make kill         — освободить порт $(PORT) (если занят)"
	@echo "    make css          — собрать TailwindCSS один раз"
	@echo "    make watch        — авто-пересборка CSS при изменении шаблонов"
	@echo ""
	@echo "  База данных:"
	@echo "    make migrate      — применить миграции"
	@echo "    make migrations   — создать новые миграции"
	@echo "    make superuser    — создать суперпользователя"
	@echo ""
	@echo "  Инструменты:"
	@echo "    make shell        — Django shell"
	@echo "    make test         — запустить тесты"
	@echo "    make install      — установить зависимости из requirements.txt"
	@echo "    make collectstatic — собрать статику для деплоя"
	@echo "    make logs         — показать последние строки всех логов"
	@echo "    make clean        — удалить .pyc, __pycache__, db.sqlite3"
	@echo ""

# ─── Разработка ──────────────────────────────────────────────────────────────
dev:
	@lsof -ti :$(PORT) | xargs kill -9 2>/dev/null; true
	$(TAILWIND) -i $(CSS_IN) -o $(CSS_OUT) --content 'templates/**/*.html'
	$(MANAGE) runserver $(PORT)

kill:
	@lsof -ti :$(PORT) | xargs kill -9 2>/dev/null && echo "Порт $(PORT) освобождён." || echo "Порт $(PORT) уже свободен."

css:
	$(TAILWIND) -i $(CSS_IN) -o $(CSS_OUT) --content 'templates/**/*.html'

watch:
	$(TAILWIND) -i $(CSS_IN) -o $(CSS_OUT) --content 'templates/**/*.html' --watch

# ─── База данных ─────────────────────────────────────────────────────────────
migrate:
	$(MANAGE) migrate

migrations:
	$(MANAGE) makemigrations

superuser:
	$(MANAGE) createsuperuser

# ─── Инструменты ─────────────────────────────────────────────────────────────
shell:
	$(MANAGE) shell

test:
	$(MANAGE) test --verbosity=2

install:
	$(PIP) install -r requirements.txt

collectstatic:
	$(TAILWIND) -i $(CSS_IN) -o $(CSS_OUT) --content 'templates/**/*.html' --minify
	$(MANAGE) collectstatic --noinput

logs:
	@echo "=== api.log ===" && tail -20 logs/api.log 2>/dev/null || echo "(пусто)"
	@echo "=== scheduler.log ===" && tail -20 logs/scheduler.log 2>/dev/null || echo "(пусто)"
	@echo "=== crawler.log ===" && tail -10 logs/crawler.log 2>/dev/null || echo "(пусто)"
	@echo "=== git.log ===" && tail -10 logs/git.log 2>/dev/null || echo "(пусто)"
	@echo "=== ai.log ===" && tail -10 logs/ai.log 2>/dev/null || echo "(пусто)"

clean:
	find . -path "./.venv" -prune -o -name "*.pyc" -delete
	find . -path "./.venv" -prune -o -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; true
	rm -f db.sqlite3
	@echo "Очищено."
