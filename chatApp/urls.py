from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from . import  views
from django.chatbot.views import web_hook

urlpatterns = [
    path('chat', views.chat, name='chat-start'),
    path('chat/owner', views.chat_owner, name='chat-owner'),
    path("webhook/", web_hook, name="webhook"),
]
