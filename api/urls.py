# app/urls.py

from django.urls import path
from .views import interaction_view

urlpatterns = [
    path('interaction/', interaction_view, name='interaction'),
]
