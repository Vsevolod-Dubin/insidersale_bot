# bot/admin.py

from django import forms
from django.db import models
from django.contrib import admin
from .models import Client, Message, Stage, Interaction, KnowledgeBlock, Assistant


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "telegram_id", "get_stage", "created_at")
    search_fields = ("name", "telegram_id")
    list_filter = ('created_at',)

    def get_stage(self, obj):
        return obj.stage.stage if hasattr(obj, 'stage') else "-"
    get_stage.short_description = "SPIN этап"


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ("client", "stage", "updated_at")
    list_filter = ("stage", "updated_at")
    raw_id_fields = ("client",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("client", "author", "short_text", "created_at")
    list_filter = ("author", "created_at")
    search_fields = ("text",)

    def short_text(self, obj):
        return obj.text[:50]
    short_text.short_description = "Текст"


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ("client", "stage_detected", "created_at")
    list_filter = ("stage_detected", "created_at")
    search_fields = ("prompt", "gpt_response", "assistant_hint")


@admin.register(KnowledgeBlock)
class KnowledgeBlockAdmin(admin.ModelAdmin):
    list_display = ("title", "updated_at")
    ordering = ("-updated_at",)

    # Увеличиваем размер поля content в админке
    formfield_overrides = {
        models.TextField: {
            'widget': forms.Textarea(attrs={'rows': 150, 'cols': 200})
        }
    }


@admin.register(Assistant)
class AssistantAdmin(admin.ModelAdmin):
    list_display = ("telegram_id", "name", "added_at")
    search_fields = ("telegram_id", "name")
