from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    url('', include('authapp.urls')),
    url('', include('properties.urls')),

]
