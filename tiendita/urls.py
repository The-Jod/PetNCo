from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from .views import  Product_ListView, Product_CreateView

"""
URL configuration for Petnco project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))


    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.vista_login.as_view(), name='inicioSesion'),
    path('accounts/signup/', views.vista_registro, name='registro')
"""


urlpatterns = [
    path('',views.home_view, name='home'),
    path('registro_citas',views.vetdate_view, name='registro'),
    path('pago/',views.pago_view,name='checkout'),
    path('carrito/',views.carrito_view,name='carrito'),
    path('productos/', views.catalogo_view, name='productos'),  
    path('productos/add/', Product_CreateView.as_view(), name='product_add'), 
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
