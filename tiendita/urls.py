from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views 
from django.contrib.auth.views import LogoutView
from . import views
from .views import  Product_ListView, Product_CreateView, RegistroUsuarioView, CustomLoginView,CalendarView
from .views import (
    VeterinariaListView, VeterinariaCreateView, VeterinariaUpdateView, VeterinariaDeleteView,
    VeterinarioListView, VeterinarioCreateView, VeterinarioUpdateView, VeterinarioDeleteView,
    ServicioListView, ServicioCreateView, ServicioUpdateView, ServicioDeleteView,
    CitaVeterinariaListView)

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
    path('late_registration',RegistroUsuarioView.as_view(), name='registeruser'),
    path('late_login',CustomLoginView.as_view(), name='loginuser'),
    path('late_logout', LogoutView.as_view(next_page='loginuser'), name='logout'),

    path('productos/', views.catalogo_view, name='productos'),  
    path('productos/add/', Product_CreateView.as_view(), name='product_add'), 
    path('productos/<int:sku>/', views.producto_detalle_modal, name='producto-modal'),
    path('agregar/<int:sku>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/<int:sku>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('limpiar/', views.limpiar_carrito, name='limpiar_carrito'),

    path('carrito/actualizar-cantidad/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('carrito/', views.carrito_view, name='carrito'),
    path('pago/', views.checkout_view, name='checkout'),
    path('checkout/webpay/return/', views.webpay_return, name='webpay_return'),
    path('orden/confirmada/<int:orden_id>/', views.orden_confirmada, name='orden_confirmada'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('procesar-pago/', views.procesar_pago_view, name='procesar_pago'),
    path('orden-confirmada/', views.orden_confirmada_view, name='orden_confirmada'),
    path('limpiar-sesion/', views.limpiar_sesion_view, name='limpiar_sesion'),
    path('webpay/retorno/', views.webpay_retorno_view, name='webpay_retorno'),
    
    path('veterinarias/',views.clinica_view, name='veterinaria'),
    path('veterinarias/add/', VeterinariaCreateView.as_view(), name='veterinaria_add'),
    path('veterinarias/edit/<int:pk>/', VeterinariaUpdateView.as_view(), name='veterinaria_edit'),
    path('veterinarias/delete/<int:pk>/', VeterinariaDeleteView.as_view(), name='veterinaria_delete'),
    
    path('veterinarios/', views.veterinario_list_view, name='veterinario'),
    path('veterinarios/', views.veterinario_view, name='veterinario'),
    path('veterinarios/add/', VeterinarioCreateView.as_view(), name='veterinario_add'),
    path('veterinarios/edit/<int:pk>/', VeterinarioUpdateView.as_view(), name='veterinario_edit'),
    path('veterinarios/delete/<int:pk>/', VeterinarioDeleteView.as_view(), name='veterinario_delete'),

    path('servicios/', views.servicio_view, name='servicio'),
    path('servicios/add/', ServicioCreateView.as_view(), name='servicio_add'),
    path('servicios/edit/<int:pk>/', ServicioUpdateView.as_view(), name='servicio_edit'),
    path('servicios/delete/<int:pk>/', ServicioDeleteView.as_view(), name='servicio_delete'),


   # URLs para renderizar el calendario y obtener datos de citas
    path('calendar/', views.CalendarView.as_view(), name='calendar'),  # Renderiza la vista del calendario
    path('api/citas/', views.CitaVeterinariaCalendarAPI.as_view(), name='citas_api'),  # API que provee los datos de las citas
    path('api/horarios-disponibles/<int:veterinario_id>/<str:fecha>/', views.HorariosDisponiblesAPI.as_view(), name='horarios_disponibles'),  # API para obtener horarios disponibles
    path('citas/agendar/', views.AgendarCitaView.as_view(), name='agendar_cita'),  # Vista para agendar citas
    path('citas/cancelar/<int:pk>/', views.CancelarCitaView.as_view(), name='cancelar_cita'),  # Vista para cancelar citas

    path('citas/', views.vetcita_list_view, name='registro'),
    
    path('perfil/', views.perfil_usuario_view, name='perfil'),
    path('mis-ordenes/', views.mis_ordenes_view, name='mis_ordenes'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('actualizar-imagen-perfil/', views.actualizar_imagen_perfil, name='actualizar_imagen_perfil'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
