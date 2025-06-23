# tests/test_interaction.py

import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch

from bot.models import Client, Message, Interaction


@pytest.mark.django_db
def test_interaction_creates_client_message_response_and_interaction():
    client = APIClient()

    payload = {
        "telegram_id": "12345",
        "name": "Тестовый Клиент",
        "text": "Привет! Хочу узнать про курс."
    }

    mock_gpt_result = {
        "reply": "Привет! С радостью расскажу про курс.",
        "assistant_hint": "Спроси, зачем ему курс.",
        "stage": "P"
    }

    with patch("bot.gpt_utils.call_gpt", return_value=mock_gpt_result):
        response = client.post("/api/interaction/", payload, format="json")

    assert response.status_code == 200
    assert response.data["reply"] == mock_gpt_result["reply"]
    assert response.data["assistant_hint"] == mock_gpt_result["assistant_hint"]

    db_client = Client.objects.get(telegram_id="12345")
    assert db_client.name == "Тестовый Клиент"

    messages = Message.objects.filter(client=db_client).order_by("created_at")
    assert len(messages) == 2
    assert messages[0].author == "client"
    assert messages[0].text == "Привет! Хочу узнать про курс."
    assert messages[1].author == "bot"
    assert messages[1].text == mock_gpt_result["reply"]

    interaction = Interaction.objects.get(client=db_client)
    assert interaction.prompt
    assert interaction.gpt_response == mock_gpt_result["reply"]
    assert interaction.assistant_hint == mock_gpt_result["assistant_hint"]
    assert interaction.stage_detected == mock_gpt_result["stage"]

    # Проверка модели Stage
    assert db_client.stage.stage == mock_gpt_result["stage"]
