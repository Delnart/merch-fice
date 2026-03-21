# Telegram Merch Bot

Telegram-бот для продажу мерчу з адмінкою в групі та покупкою в ПП.

## Що реалізовано

- Webhook-бот на aiogram + FastAPI для Vercel
- Прив'язка адмін-групи командою /bind_admin_chat
- Адмін-функції в групі:
  - /add_product Назва | Опис
  - /set_sizes product_id | S:500,M:550,L:600
  - /set_price product_id | SIZE | 500
  - /set_text product_id | Новий опис
  - /set_photo product_id
  - /archive_product product_id
  - /unarchive_product product_id
  - /products
  - /set_welcome Текст
- Приватна покупка:
  - /start
  - /catalog
  - /cart
  - checkout через inline-кнопки
- Нотифікація нового замовлення в адмін-групу
- Кнопки зміни статусу замовлення в адмін-групі
- Автоматичне повідомлення користувачу про зміну статусу

## Структура

- api/index.py
- app/main.py
- app/config.py
- app/db/
- app/bot/
- app/services/

## Налаштування

1. Створіть .env на основі .env.example
2. Встановіть залежності:

```bash
pip install -r requirements.txt
```

3. Для локального запуску:

```bash
uvicorn app.main:app --reload --port 8000
```

## Підготовка webhook

1. Вкажіть APP_BASE_URL у .env
2. Відкрийте:

- GET /setup/webhook
- GET /setup/delete_webhook

Приклад:

```bash
curl https://your-domain.vercel.app/setup/webhook
```

## Deploy на Vercel

1. Імпортуйте репозиторій у Vercel
2. Додайте env variables:
- BOT_TOKEN
- WEBHOOK_SECRET
- DATABASE_URL
- APP_BASE_URL
- ADMIN_DEFAULT_CURRENCY
3. Після деплою викличте /setup/webhook

## Примітки по БД

- Підтримується PostgreSQL через DATABASE_URL
- Таблиці створюються автоматично при старті

## Формат адмін-команд

- Додати товар:

```text
/add_product Hoodie FICE | Щільний чорний худі з логотипом
```

- Оновити розміри:

```text
/set_sizes 1 | S:1200,M:1250,L:1300,XL:1350
```

- Оновити одну ціну:

```text
/set_price 1 | M | 1275
```

- Оновити опис:

```text
/set_text 1 | Новий опис товару
```

- Оновити фото:

```text
/set_photo 1
```

Після команди надішліть фото наступним повідомленням у адмін-групі.
