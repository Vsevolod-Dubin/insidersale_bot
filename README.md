# 🤖 Insidersale Telegram Bot

A Django-powered Telegram bot that helps assistants sell an online course using OpenAI and the SPIN selling technique.

## 📌 Features

- Telegram integration with assistant-client flow
- SPIN-stage detection: Situation, Problem, Implication, Need
- OpenAI GPT-based message generation
- Dynamic prompt creation from Excel-based knowledge base
- Client and message history stored in SQLite
- Admin panel to manage clients, messages, and SPIN stages

## 🛠 Tech Stack

- Python 3.10+
- Django 4.2+
- python-telegram-bot
- OpenAI API
- SQLite (with optional Persistent Disk)

Both the Django server and Telegram bot are run in a single process using `serve_and_run_bot.py`.

### How to run locally

```bash
git clone https://github.com/yourusername/insidersale_bot.git
cd insidersale_bot
python -m venv env
source env/bin/activate  # or .\env\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env     # create and edit your .env file
python manage.py migrate
python serve_and_run_bot.py  # runs both Django and the bot together
```

## 📁 Project Structure

```
insidersale_bot/
│
├── bot/               # Telegram bot logic (handlers, OpenAI, etc.)
├── core/              # Django core settings and URLs
├── templates/         # (optional) Templates for admin customization
├── serve_and_run_bot.py  # Script to run Django and the bot together
├── db.sqlite3         # Local database
├── .env               # Environment variables (Telegram token, OpenAI key)
├── requirements.txt   # Project dependencies
└── manage.py
```

---

<details>
<summary>🇷🇺 Нажмите, чтобы прочитать описание на русском</summary>

# 🤖 Insidersale Telegram Bot

Telegram-бот на Django, помогающий ассистентам продавать онлайн-курс с помощью OpenAI и техники SPIN-продаж.

## 📌 Возможности

- Интеграция с Telegram (ассистент → клиент)
- Автоматическое определение этапа SPIN (S, P, I, N)
- Генерация ответов с помощью OpenAI GPT
- Загрузка базы знаний из Excel-файла
- Сохранение клиентов и истории сообщений в SQLite
- Админка для просмотра клиентов и диалогов

## 🛠 Технологии

- Python 3.10+
- Django 4.2+
- python-telegram-bot
- OpenAI API
- SQLite (с возможностью подключения Persistent Disk)

PostgreSQL и вебхуки не требуются.

Бот и сервер Django запускаются одновременно через `serve_and_run_bot.py`.

### Как запустить локально

```bash
git clone https://github.com/yourusername/insidersale_bot.git
cd insidersale_bot
python -m venv env
source env/bin/activate  # или .\env\Scripts\activate на Windows
pip install -r requirements.txt
cp .env.example .env     # создайте и настройте .env файл
python manage.py migrate
python serve_and_run_bot.py  # запускает и Django, и Telegram-бота вместе
```

</details>