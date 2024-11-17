from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from . import views
from .views import  Product_ListView, Product_CreateView, RegistroUsuarioView

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
    path('login',RegistroUsuarioView.as_view(), name='login'),
    path('pago/',views.pago_view,name='checkout'),
    path('carrito/',views.carrito_view,name='carrito'),
    path('productos/', views.catalogo_view, name='productos'),  
    path('productos/add/', Product_CreateView.as_view(), name='product_add'), 
    path('productos/<int:sku>/', views.producto_detalle_modal, name='producto-modal'),
       # Vista principal que contiene todos los modales
    path('citas/', views.lista_citas, name='lista_citas'),
    
    # Endpoints para AJAX
    path('api/citas/crear/', views.crear_cita, name='crear_cita'),
    path('api/citas/<int:pk>/', views.crear_cita, name='obtener_cita'),
    path('api/citas/<int:pk>/editar/', views.editar_cita, name='editar_cita'),
    path('api/citas/<int:pk>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    
    path('api/calendario/', views.api_citas_calendario, name='api_calendario'),
    path('api/horarios-disponibles/', views.api_horarios_disponibles, name='api_horarios_disponibles'),
    path('api/veterinarios/', views.obtener_veterinarios, name='api_veterinarios'),

    
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
