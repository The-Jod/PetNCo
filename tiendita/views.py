from django.shortcuts import render
from django.contrib.auth import views as auth_views
from django.urls import include, path

# Aqui van las famosas vistas, no confundir

def reg_view(request):
    return render(request, 'lateregistration/registro.html')

def login_view(request):
    return render(request, 'lateregistration/login.html')

def home_view(request):
    return render(request, 'home.html')

def vetdate_view(request):
    return render(request, 'cita.html')

def storefront_view(request):
    return render(request, 'catalogo.html')