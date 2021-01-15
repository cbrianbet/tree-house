from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('', views.login, name='web-login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('signup/', views.signup, name='register'),
    path('logout/', views.logout_request, name='logout'),

]
