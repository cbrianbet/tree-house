from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from messengerbot import MessengerClient, messages, attachments, templates, elements
from chatbot import Chat, register_call
import wikipedia


@login_required
def chat(request):

    context = {
        'user': request.user,
    }
    return render(request, 'chatApp/chat.html', context)


@login_required
def chat_owner(request):


    context = {
        'user': request.user,
    }
    return render(request, 'chatApp/chat_with.html', context)


@register_call("whoIs")
def who_is(session, query):
    try:
        return wikipedia.summary(query)
    except:
        pass
    for new_query in wikipedia.search(query):
        try:
            return wikipedia.summary(new_query)
        except:
            pass
    return "I don't know about " + query