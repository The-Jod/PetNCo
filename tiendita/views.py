from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.urls import path

# Aqui van las famosas vistas, no confundir

def vista_registro(request):
    return render(request, 'lateregistration/registro.html')

def vista_login(request):
    return render(request, 'lateregistration/login.html')

