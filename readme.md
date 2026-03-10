# RR Lazy Damage / Payment Toolkit (Web migration)

Проект переведён в веб-формат (MVP):
- Flask backend для расчётов,
- Firefox extension для импорта cookies из браузера,
- web UI для запуска расчётов.

Также сохранены существующие desktop-инструменты (Tkinter/PyQt) как fallback.

---

## Что уже работает

### Веб
- `web_app/app.py` — Flask API + простая веб-страница
  - список активных заказов,
  - статус сессии,
  - запуск расчёта по заказу,
  - выгрузка CSV.
- `web_extension_firefox/` — Firefox extension
  - читает cookies (`PHPSESSID`, `rr`, `rr_add`, `rr_f`, `rr_id`) для `rivalregions.com`/`rivalka.ru`,
  - отправляет их в backend endpoint `/api/session/import-cookies`.

### Legacy desktop (по-прежнему в репозитории)
- `new_pay_calc.py`
- `StatWindow.py`
- `statistics.py`
- `summary.py`

---

## Архитектура веб-части

- Конфиг БД: `db_config.py`
- ORM модели: `new_models.py`
- Flask backend: `web_app/app.py`
- Хранилище импортированных cookies: `web_app/session_store.py` (локальный JSON-файл)
- UI: `web_app/templates/index.html`
- Browser bridge: `web_extension_firefox/manifest.json`, `popup.html`, `popup.js`

---

## Установка

```bash
pip install -r requirements.txt
```

> Для `mysql+pymysql://...` нужен установленный драйвер `pymysql`.

---

## Настройка подключения к БД

Строка подключения ищется в порядке:
1. `DATABASE_URL`
2. `msql_connection_string.txt`
3. `msql_connecting_string.txt`

Пример:

```text
mysql+pymysql://USER:PASSWORD@HOST:3306/DB?charset=utf8mb4
```

---

## Запуск веб-бэкенда

```bash
python web_app/app.py
```

После запуска открыть:
- `http://localhost:5000/`

---

## Установка Firefox extension (вручную)

1. Откройте `about:debugging#/runtime/this-firefox`
2. Нажмите **Load Temporary Add-on**
3. Выберите файл `web_extension_firefox/manifest.json`
4. Откройте `rivalregions.com` (или `rivalka.ru`) и авторизуйтесь
5. Нажмите иконку расширения → **Отправить cookies**

После этого backend увидит сессию в `/api/session/status`.

После авторизации и загрузки cookies на главной появляется меню:
- расчёт по активным заказам из БД;
- ручной расчёт по войне (`war_id`, `price`, `stop_at`, `limit`, `is_attack`) с выгрузкой CSV.

---


## Telegram-авторизация (обязательно для API)

Backend поддерживает вход через Telegram Login Widget.

Нужно задать переменные окружения:

```bash
export TELEGRAM_BOT_TOKEN="<bot_token>"
export TELEGRAM_BOT_USERNAME="<bot_username_without_@>"
export WEB_SECRET_KEY="<random_secret_for_flask_session>"
```

После этого на главной странице появится кнопка входа через Telegram.
Все рабочие API-методы (`/api/orders`, `/api/session/*`, `/api/calculate/*`) требуют авторизацию.

---

## API (MVP)

- `GET /api/orders` — список активных заказов
- `GET /api/session/status` — есть ли загруженная cookie-сессия
- `POST /api/session/import-cookies` — импорт cookies из extension
- `POST /api/calculate/<order_id>` — расчёт по заказу (JSON)
- `POST /api/calculate/<order_id>/csv` — расчёт по заказу и отдача CSV
- `POST /api/war/calculate` — ручной кек-калькулятинг по параметрам войны (JSON)
- `POST /api/war/calculate/csv` — ручной кек-калькулятинг по параметрам войны и отдача CSV
- `GET /api/crm/export` — CRM-ready snapshot (заказы + статус сессии + базовая статистика)

---

## Важные ограничения MVP

1. Cookies сейчас хранятся локально в `web_app/runtime/session.json` (без шифрования).
2. Нет multi-user изоляции сессий.
3. Нет полноценной авторизации/ролей в web UI.
4. UI пока технический (минимальный).

---

## Следующие шаги

1. Добавить авторизацию (JWT/session).
2. Перейти на защищённое хранение сессий (шифрование, TTL, revoke).
3. Сделать нормальный frontend (React/Vue) вместо базового HTML.
4. Вынести расчёт в сервисный слой + очередь задач (Celery/RQ).
5. Добавить тесты на API и extension-интеграцию.


### Telegram виджет не отображается / Bot domain invalid
Проверьте:
- приложение открыто по домену, который указан в BotFather (`/setdomain`),
- используется HTTPS (для локальной разработки используйте tunnel: ngrok/cloudflared),
- `TELEGRAM_BOT_USERNAME` совпадает с текущим ботом,
- в блоке "Авторизация" на странице показаны корректные `Telegram bot` и `Auth URL`.



---

## Интеграция с бесплатными CRM

Да, можно интегрировать текущую БД и расчёты с free/open-source CRM без переписывания всей системы.

Рекомендуемые варианты:
- **EspoCRM (open-source)** — удобные сущности, API, self-hosted.
- **SuiteCRM (open-source)** — классический CRM-подход, много готовых модулей.
- **Odoo Community** — если нужна CRM + процессы/учёт в одном месте.

Практичный путь с минимальным риском:
1. Использовать `GET /api/crm/export` как источник данных (orders/session/stats).
2. Подключить n8n/Make/Zapier (или прямой integration script) для передачи в CRM.
3. В CRM создать сущности:
   - `War Orders` (id/name/url/price/limit/end_date),
   - `War Calculations` (rows с damage/sum/profile_url),
   - `Users/Sessions` (кто загрузил cookies, когда).
4. Добавить webhook-цепочку: расчёт в backend → событие/вставка в CRM.

Так вы получите формы, отчёты и автоматизацию в CRM, сохранив текущую бизнес-логику расчётов в этом проекте.


---

## Встроенная CRM

Я выбрал лёгкий путь: встроенная **mini CRM в стиле EspoCRM** внутри текущего Flask-приложения.

Что доступно:
- `GET /crm` — CRM-страница (доступ после Telegram-авторизации),
- автоматический переход в CRM сразу после логина,
- таблица активных заказов из БД,
- локальные CRM-лиды (создание и просмотр).

CRM API:
- `GET /api/crm/leads` — список лидов,
- `POST /api/crm/leads` — создать лид,
- `GET /api/crm/export` — экспорт агрегированного snapshot для интеграций.

Хранилище лидов: `web_app/runtime/crm_leads.json`.
