# bot/models.py

from django.db import models


class Client(models.Model):
    telegram_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Client {self.telegram_id}"


class Stage(models.Model):
    STAGE_CHOICES = [
        ("S", "Situation"),
        ("P", "Problem"),
        ("I", "Implication"),
        ("N", "Need-Payoff"),
    ]

    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name='stage')
    stage = models.CharField(max_length=1, choices=STAGE_CHOICES)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client} - {self.get_stage_display()}"


class Message(models.Model):
    AUTHOR_CHOICES = [
        ("client", "Client"),
        ("assistant", "Assistant"),
        ("bot", "Bot"),
    ]
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='messages')
    author = models.CharField(max_length=10, choices=AUTHOR_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.author}] {self.text[:30]}"


class Interaction(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='interactions')
    prompt = models.TextField()
    gpt_response = models.TextField()
    assistant_hint = models.TextField()
    stage_detected = models.CharField(max_length=1, choices=Stage.STAGE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interaction with {self.client} at {self.created_at}"


class KnowledgeBlock(models.Model):
    title = models.CharField(max_length=255, default="База знаний")
    content = models.TextField(help_text="Вставьте сюда текст базы знаний")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} (обновлено {self.updated_at:%d.%m.%Y %H:%M})"


class Assistant(models.Model):
    telegram_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Assistant {self.telegram_id}"


class ActiveContext(models.Model):
    assistant_telegram_id = models.CharField(max_length=100, unique=True)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
