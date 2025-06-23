# bot/gpt_utils.py

from openai import OpenAI
import os
import re
from dotenv import load_dotenv
from asgiref.sync import sync_to_async

from .models import Message, Stage, KnowledgeBlock


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_latest_knowledge_block() -> str:
    block = KnowledgeBlock.objects.order_by("-updated_at").first()
    return block.content if block else ""


def get_history_text(client, limit=10) -> str:
    """
    Собирает последние N сообщений клиента и бота.
    Возвращает в формате: "Клиент: ... \n Бот: ..."
    """

    history = Message.objects.filter(client=client).order_by('created_at')[:limit]

    lines = []
    for msg in history:
        prefix = {
            "client": "Клиент:",
            "bot": "Бот:",
            "assistant": "Ассистент:"
        }.get(msg.author, "Сообщение:")
        lines.append(f"{prefix} {msg.text}")
    return "\n".join(lines)


def stage_letter_to_label(stage: str) -> str:
    """
    Преобразует символ этапа SPIN (S/P/I/N) в человекочитаемый текст
    """
    return {
        'S': 'S — Situation (ситуационные вопросы)',
        'P': 'P — Problem (проблемные вопросы)',
        'I': 'I — Implication (вопросы-усугубления)',
        'N': 'N — Need-Payoff (ценностные вопросы)'
    }.get(stage, 'S — Situation (ситуационные вопросы)')


def generate_prompt(client, new_message_text: str) -> str:
    """
    Формирует prompt для GPT: база знаний + история + новое сообщение.
    Ожидается: ответ клиенту, подсказка ассистенту и SPIN-этап.
    """

    client_name = client.name or f"ID {client.telegram_id}"
    history_text = get_history_text(client)
    knowledge_block = get_latest_knowledge_block()
    try:
        stage_obj = Stage.objects.get(client=client)
        current_stage = stage_letter_to_label(stage_obj.stage)
        spin_line = f"Текущий SPIN-этап клиента: {current_stage}\n"
    except Stage.DoesNotExist:
        spin_line = "Текущий SPIN-этап клиента: S — Situation (ситуационные вопросы)\n"

    return f"""
{knowledge_block}


Клиент по имени {client_name} ведет переписку.

{spin_line}

История сообщений
{history_text}

Новое сообщение клиента:
\"{new_message_text}\"

Ответь клиенту так, как если бы ты был опытным ассистентом, продающим онлайн-курс.
Отвечай на «вы»(пока он сам не попросит перейти на "ты"), используй методику SPIN, развивай диалог.

⚠️ Ответ обязательно верни в таком формате:

Ответ клиенту:
{{здесь текст ответа клиенту}}

Подсказка ассистенту:
{{что порекомендуешь ассистенту сделать дальше в соответствии со SPIN методикой — уточнить, спросить и т.д.}}

#Этап: S / P / I / N (например, #Этап: P, #Этап: I и т.д.)
"""


def extract_stage(text: str) -> str:
    """
    Извлекает SPIN-этап из строки вида #Этап: S.
    По умолчанию — S.
    """

    match = re.search(r'#Этап:\s*([SPIN])', text)
    return match.group(1) if match else 'S'


def clean_reply(reply: str) -> str:
    """
    Удаляет строку с #Этап: ... перед показом клиенту
    """
    return re.sub(r'#Этап:\s*[SPIN]', '', reply).strip()


def call_gpt(prompt: str) -> dict:
    """
    Отправляет prompt в GPT и парсит:
    - Ответ клиенту
    - Подсказку ассистенту
    - SPIN-этап
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты ассистент по продажам онлайн-курса, общающийся в чате."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )

    full_reply = response.choices[0].message.content
    print("GPT ответил:\n", full_reply)
    stage = extract_stage(full_reply)
    reply_match = re.search(r"Ответ клиенту:\s*(.*?)\n+Подсказка ассистенту:", full_reply, re.DOTALL)
    hint_match = re.search(r"Подсказка ассистенту:\s*(.*?)\n+#Этап:", full_reply, re.DOTALL)

    reply = reply_match.group(1).strip() if reply_match else "Извините, не удалось сгенерировать ответ."
    assistant_hint = hint_match.group(1).strip() if hint_match else "Добавь уточняющий вопрос в стиле SPIN."

    return {
        "reply": reply,
        "assistant_hint": assistant_hint,
        "stage": stage
    }


async def generate_assistant_prompt(client, assistant_question: str) -> str:
    """
    Формирует prompt для GPT на вопрос ассистента по активному клиенту.
    """

    client_name = client.name or f"ID {client.telegram_id}"
    knowledge_block = await sync_to_async(get_latest_knowledge_block)()

    history = await sync_to_async(list)(
        Message.objects.filter(client=client).order_by("created_at")[:10]
    )

    lines = []
    for msg in history:
        prefix = {
            "client": "Клиент:",
            "bot": "Бот:",
            "assistant": "Ассистент:"
        }.get(msg.author, "Сообщение:")
        lines.append(f"{prefix} {msg.text}")
    history_text = "\n".join(lines)

    return f"""
{knowledge_block}

Клиент по имени {client_name} ведет переписку.

История сообщений:
{history_text}

Вопрос ассистента:
"{assistant_question}"

Ты — опытный ассистент по продажам. Ответь своему коллеге, который интересуется этим клиентом.
Отвечай ясно и кратко. Не нужно обращаться к клиенту. Просто дай суть.
"""


def call_gpt_plain(prompt: str) -> str:
    """
    Отправляет prompt в GPT и возвращает просто текст без парсинга.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Ты — помощник по продажам. Отвечай коллеге по клиенту."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
