# Руководство по настройке: Google Cloud Console + Django Admin

---

## Часть 1: Google Cloud Console

### Шаг 1 — Создать проект в Google Cloud

1. Открой [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. В верхней панели нажми на выпадающий список проектов → **"New Project"**
3. Назови проект: `seo-dashboard` (или любое имя)
4. Нажми **Create**
5. Убедись, что новый проект выбран в верхней панели

---

### Шаг 2 — Включить Search Console API

1. В левом меню: **APIs & Services → Library**
2. В поиске напечатай: `Google Search Console API`
3. Выбери **"Google Search Console API"**
4. Нажми **Enable**

> Для фазы 2 аналогично включи **Google Analytics Data API** (GA4)

---

### Шаг 3 — Настроить OAuth2 Consent Screen

1. В левом меню: **APIs & Services → OAuth consent screen**
2. Выбери **External** → нажми **Create**
3. Заполни обязательные поля:
   - **App name**: `SEO Dashboard`
   - **User support email**: твой email
   - **Developer contact information**: твой email
4. Нажми **Save and Continue**
5. На шаге **Scopes** нажми **Add or Remove Scopes**, найди и добавь:
   - `https://www.googleapis.com/auth/webmasters.readonly`
6. Нажми **Save and Continue**
7. На шаге **Test users** нажми **Add Users**, добавь свой Google аккаунт
8. Нажми **Save and Continue** → **Back to Dashboard**

> **Важно**: пока приложение в статусе "Testing", OAuth работает только для добавленных test users. Этого достаточно для MVP.

---

### Шаг 4 — Создать OAuth2 Credentials

1. В левом меню: **APIs & Services → Credentials**
2. Нажми **+ Create Credentials → OAuth client ID**
3. **Application type**: Web application
4. **Name**: `SEO Dashboard Local`
5. В разделе **Authorized redirect URIs** нажми **+ Add URI** и добавь:
   ```
   http://127.0.0.1:8001/integrations/google/callback/
   ```
6. Нажми **Create**
7. Появится окно с **Client ID** и **Client Secret** — скопируй оба значения
8. Нажми **Download JSON** — сохрани файл как `credentials.json`

---

### Шаг 5 — Сохранить credentials в проект

1. Скопируй скачанный файл в папку проекта:
   ```bash
   cp ~/Downloads/client_secret_*.json /Users/colizej/Documents/webApp/devtool/credentials/google_oauth.json
   ```

2. Создай папку если её нет:
   ```bash
   mkdir -p /Users/colizej/Documents/webApp/devtool/credentials
   ```

3. Открой файл `.env` в корне проекта и заполни поля:
   ```
   GOOGLE_CLIENT_ID=ваш_client_id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=ваш_client_secret
   GOOGLE_CREDENTIALS_FILE=credentials/google_oauth.json
   ```

> Папка `credentials/` уже добавлена в `.gitignore` — секреты не попадут в репозиторий.

---

### Шаг 6 — Убедиться, что сайты верифицированы в GSC

1. Открой [https://search.google.com/search-console/](https://search.google.com/search-console/)
2. Убедись, что все три сайта добавлены и верифицированы:
   - `piecedetheatre.be`
   - `prava.be`
   - `clikme.ru`
3. Для каждого сайта запомни тип property:
   - **Domain property**: `sc-domain:prava.be` ← рекомендуется, охватывает http/https/www
   - **URL prefix property**: `https://prava.be/` ← для конкретного хоста

---

## Часть 2: Добавить сайты в Django Admin

### Запустить сервер

```bash
cd /Users/colizej/Documents/webApp/devtool
make dev
```

Открой в браузере: **http://127.0.0.1:8001/admin/projects/project/add/**

Логин: `admin` | Пароль: `admin123`

---

### Проект 1: piecedetheatre.be

| Поле | Значение |
|------|----------|
| **Название** | Pièce de Théâtre |
| **Slug** | *(оставить пустым — заполнится автоматически)* |
| **Домен** | piecedetheatre.be |
| **Платформа** | WordPress *(или выбери нужное)* |
| **Sitemap URL** | https://piecedetheatre.be/sitemap.xml |
| **GSC Property** | sc-domain:piecedetheatre.be |
| **GA4 Property ID** | *(оставь пустым пока не знаешь ID)* |
| **Путь к репозиторию** | /Users/colizej/projects/piecedetheatre *(твой путь)* |
| **Git Remote URL** | git@github.com:colizej/piecedetheatre.git *(твой репо)* |
| **Активен** | ✓ |

---

### Проект 2: prava.be

| Поле | Значение |
|------|----------|
| **Название** | Prava.be |
| **Slug** | *(оставить пустым)* |
| **Домен** | prava.be |
| **Платформа** | Django *(или нужная)* |
| **Sitemap URL** | https://prava.be/sitemap.xml |
| **GSC Property** | sc-domain:prava.be |
| **GA4 Property ID** | *(оставь пустым пока)* |
| **Путь к репозиторию** | /Users/colizej/projects/prava *(твой путь)* |
| **Git Remote URL** | git@github.com:colizej/prava.git *(твой репо)* |
| **Активен** | ✓ |

---

### Проект 3: clikme.ru

| Поле | Значение |
|------|----------|
| **Название** | Clikme.ru |
| **Slug** | *(оставить пустым)* |
| **Домен** | clikme.ru |
| **Платформа** | *(выбери нужное)* |
| **Sitemap URL** | https://clikme.ru/sitemap.xml |
| **GSC Property** | sc-domain:clikme.ru |
| **GA4 Property ID** | *(оставь пустым пока)* |
| **Путь к репозиторию** | /Users/colizej/projects/clikme *(твой путь)* |
| **Git Remote URL** | git@github.com:colizej/clikme.git *(твой репо)* |
| **Активен** | ✓ |

---

### Как узнать GA4 Property ID

1. Открой [https://analytics.google.com/](https://analytics.google.com/)
2. Выбери нужный ресурс (аккаунт → ресурс)
3. В левом меню внизу: **Admin (шестерёнка)**
4. В колонке **Property**: нажми **Property Settings**
5. Скопируй **Property ID** — это число вида `123456789`
6. Вставь в поле **GA4 Property ID** и нажми **Save**

---

### Как найти правильное название GSC Property

1. Открой [https://search.google.com/search-console/](https://search.google.com/search-console/)
2. В левом верхнем углу нажми на выпадающий список ресурсов
3. Наведи на нужный сайт — увидишь точное название:
   - Если иконка глобуса → **Domain property** → вводи `sc-domain:yourdomain.com`
   - Если иконка лупы → **URL prefix** → вводи полный URL `https://yourdomain.com/`

---

## Итоговый чеклист

### Google Cloud Console
- [ ] Проект создан
- [ ] Search Console API включён
- [ ] OAuth Consent Screen настроен (External, Test users добавлены)
- [ ] OAuth2 Client ID создан (Web application)
- [ ] Redirect URI добавлен: `http://127.0.0.1:8001/integrations/google/callback/`
- [ ] `credentials/google_oauth.json` сохранён в проект
- [ ] `.env` заполнен: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

### Search Console
- [ ] piecedetheatre.be верифицирован
- [ ] prava.be верифицирован
- [ ] clikme.ru верифицирован

### Django Admin
- [ ] Проект piecedetheatre.be добавлен с GSC property
- [ ] Проект prava.be добавлен с GSC property
- [ ] Проект clikme.ru добавлен с GSC property
- [ ] GA4 Property ID добавлен для каждого сайта (опционально сейчас)

---

После выполнения всего — готовы к реализации **Фазы 1**: OAuth2 авторизация + импорт данных GSC.
