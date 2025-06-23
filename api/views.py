# api/views.py

from rest_framework.decorators import api_view
from rest_framework.response import Response

from bot.models import Client, Message, Interaction, Stage
from bot.gpt_utils import generate_prompt, call_gpt


@api_view(['POST'])
def interaction_view(request):
    """
    Обрабатывает сообщение от клиента (через пересылку):
    — сохраняет в БД,
    — формирует prompt,
    — получает ответ от GPT,
    — сохраняет результат с SPIN и подсказкой.
    """

    telegram_id = request.data.get('telegram_id')
    name = request.data.get('name')
    text = request.data.get('text')

    if not telegram_id or not text:
        return Response({"error": "Недостаточно данных"}, status=400)

    # 1. Ищем клиента по telegram_id, если не найден — создаём
    client, created = Client.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={"name": name}
    )

    # 2. Сохраняем входящее сообщение от клиента
    Message.objects.create(
        client=client,
        text=text,
        author="client"
    )

    # 3. Формируем prompt, отправляем его в GPT и получаем ответ + SPIN + hint
    prompt = generate_prompt(client, text)
    gpt_result = call_gpt(prompt)

    reply = gpt_result["reply"]
    hint = gpt_result["assistant_hint"]
    stage = gpt_result["stage"]

    # 4. Сохраняем ответ бота как сообщение
    Message.objects.create(
        client=client,
        text=reply,
        author="bot"
    )

    # 5. Сохраняем Interaction (с prompt, ответом, hint и SPIN-этапом)
    Interaction.objects.create(
        client=client,
        prompt=prompt,
        gpt_response=reply,
        assistant_hint=hint,
        stage_detected=stage
    )

    # 6. Обновляем SPIN-этап клиента (таблица Stage) — создаём или обновляем
    Stage.objects.update_or_create(
        client=client,
        defaults={"stage": stage}
    )

    return Response(gpt_result)