# bot/bot_main.py

import os
from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")  # fallback по умолчанию

import django
django.setup()

import requests
import re

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes, CommandHandler

from openai import OpenAI
from asgiref.sync import sync_to_async

from bot.messages import message_start
from bot.models import Client, Stage, Assistant, ActiveContext
from bot.gpt_utils import (
    generate_prompt,
    call_gpt,
    generate_assistant_prompt,
    call_gpt_plain,
)


# Функция для удаления emoji из текста
def remove_emojis(text: str) -> str:
    """
    Удаляет все emoji из строки.
    """
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
        u"\U00002700-\U000027BF"
        u"\U0001F900-\U0001F9FF"
        u"\U0001FA70-\U0001FAFF"
        u"\U00002600-\U000026FF"
        "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text).strip()


@sync_to_async
def is_allowed_assistant(telegram_id: int) -> bool:
    return Assistant.objects.filter(telegram_id=str(telegram_id)).exists()


openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает сообщение от ассистента:
    — сохраняет клиента по пересылке или reply,
    — отвечает на вопросы по активному клиенту.
    """

    message = update.message

    # Проверяем, есть ли Telegram ID ассистента в списке разрешённых
    assistant_id = update.effective_user.id
    if not await is_allowed_assistant(assistant_id):
        await update.message.reply_text(
            "⛔ Доступ запрещён.\n\n"
            "Обратитесь к руководителю, чтобы получить доступ.\n"
            "Понадобится ваш Telegram ID.\n\n"
            "📌 Как его узнать:\n"
            "1. Откройте @userinfobot\n"
            "2. Нажмите Start — бот покажет ваш ID"
        )
        return

    if not message or not message.text:
        await update.message.reply_text("Пожалуйста, отправьте текстовое сообщение.")
        return

    # Вариант 0.5: переключение контекста по ответу на пересланное сообщение
    if message.reply_to_message and message.reply_to_message.forward_from:
        client = message.reply_to_message.forward_from
        client_id = client.id
        client_name = client.full_name

        client_obj, _ = await sync_to_async(Client.objects.get_or_create)(
            telegram_id=client_id,
            defaults={"name": client_name}
        )
        await sync_to_async(ActiveContext.objects.update_or_create)(
            assistant_telegram_id=str(assistant_id),
            defaults={"client": client_obj}
        )

        await message.reply_text(f"✅ Контекст переключён на клиента: {client_name}")

    # Вариант 1: пересланное сообщение от клиента
    if message.forward_date:
        forwarded_text = message.text
        client = message.forward_from
        if not client:
            await message.reply_text(
                    "Не удалось определить отправителя пересланного сообщения.\n"
                    "Скорее всего, пользователь скрыл свой аккаунт от пересылок.\n\n"
                    "Попроси клиента разрешить пересылку сообщений в настройках Telegram:\n"
                    "Settings → Privacy → Forwarded Messages → Everybody"
            )
            return

        client_id = client.id
        client_name = client.full_name

        payload = {
            "telegram_id": client_id,
            "name": client_name,
            "text": forwarded_text
        }

        # Сохраняем активного клиента для ассистента
        client_obj, _ = await sync_to_async(Client.objects.get_or_create)(
            telegram_id=client_id,
            defaults={"name": client_name}
        )
        await sync_to_async(ActiveContext.objects.update_or_create)(
            assistant_telegram_id=str(assistant_id),
            defaults={"client": client_obj}
        )

        try:
            response = requests.post(f"{API_URL}/api/interaction/", json=payload)
            response.raise_for_status()
            data = response.json()

            print("Ответ от сервера:", data)

            await message.reply_text(data.get("reply", "Не удалось получить ответ от сервера."))
            await message.reply_text(data.get("assistant_hint", "Нет подсказки от ассистента."))

        except requests.exceptions.RequestException as e:
            print("Ошибка при обращении к серверу:", e)
            await message.reply_text("Произошла ошибка при обращении к серверу.")
        return

    # Вариант 2: обычное сообщение — уточнение по последнему клиенту
    active_context = await sync_to_async(
        lambda: ActiveContext.objects.filter(assistant_telegram_id=str(assistant_id)).first()
    )()

    if active_context:
        client = await sync_to_async(lambda: active_context.client)()
        stage_obj = await sync_to_async(Stage.objects.filter(client=client).first)()
        if stage_obj:
            stage_map = {
                "S": "S — Situation (ситуационные вопросы)",
                "P": "P — Problem (проблемные вопросы)",
                "I": "I — Implication (усугубляющие вопросы)",
                "N": "N — Need-payoff (ценностные вопросы)"
            }
            stage_label = stage_map.get(stage_obj.stage, "S — Situation")
            spin_line = f"📌 Текущий SPIN-этап клиента: {stage_label}\n\n"
        else:
            spin_line = "📌 Текущий SPIN-этап клиента: S — Situation (ситуационные вопросы)\n\n"

        assistant_question = message.text.strip()
        prompt = await generate_assistant_prompt(client, assistant_question)
        reply = await sync_to_async(call_gpt_plain)(prompt)
        await message.reply_text(spin_line + reply)
        return

    # 🆕 Если ни один клиент ещё не переслан
    await message.reply_text(
        "Пожалуйста, сначала перешлите сообщение от клиента"
    )


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(message_start)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("start", handle_start))
    print("Бот запущен.")
    
    app.run_polling()


if __name__ == "__main__":
    main()