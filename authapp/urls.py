from django.conf.urls import url
from django.contrib import admin
from django.urls import path
from . import  views

urlpatterns = [
    path('', views.login, name='web-login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('checkusername/', views.profile, name='check-username'),
    path('change_password/', views.change_password, name='change_password'),
    path('signup/', views.signup, name='register'),
    path('logout/', views.logout_request, name='logout'),

]
