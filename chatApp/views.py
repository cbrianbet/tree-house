from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from messengerbot import MessengerClient, messages, attachments, templates, elements
import json,wikipedia,urllib,os
from chatbot import Chat, register_call
import wikipedia


@login_required
def chat(request):

    context = {
        'user': request.user,
    }
    return render(request, 'chatApp/chat.html', context)