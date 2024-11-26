from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views 
from django.contrib.auth.views import LogoutView
from . import views
from .views import (
    RegistroUsuarioView,
    CustomLoginView,
    Product_CreateView,
    PerfilVeterinarioView,
    PrecioPersonalizadoView,
    DisponibilidadVeterinarioView,
    DisponibilidadAPIView,
    DisponibilidadDetailAPIView,
    DisponibilidadClonarAPIView,
    DisponibilidadEventosAPIView,
    ServicioView,
    ServicioPersonalizadoView,
    GestionServiciosView,
    GestionServiciosAPIView,
    VeterinarioPerfilUpdateView,
    VeterinarioImagenUpdateView,
    ResenasVeterinarioView,
    ServiciosVeterinarioView,
    ServicioDeleteView,
    ServicioToggleEstadoView,
    # Otras vistas que necesites...
)

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
    path('', views.home_view, name='home'),
    path('late_registration', RegistroUsuarioView.as_view(), name='registeruser'),
    path('late_login', CustomLoginView.as_view(), name='loginuser'),
    path('late_logout', LogoutView.as_view(next_page='loginuser'), name='logout'),

    # Productos
    path('productos/', views.catalogo_view, name='productos'),  
    path('productos/add/', Product_CreateView.as_view(), name='product_add'), 
    path('productos/<int:sku>/', views.producto_detalle_modal, name='producto-modal'),
    
    # Carrito
    path('agregar/<int:sku>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('eliminar/<int:sku>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('limpiar/', views.limpiar_carrito, name='limpiar_carrito'),
    path('carrito/actualizar-cantidad/', views.actualizar_cantidad, name='actualizar_cantidad'),
    path('carrito/', views.carrito_view, name='carrito'),

    # Checkout y pagos
    path('pago/', views.checkout_view, name='checkout'),
    path('checkout/webpay/return/', views.webpay_return, name='webpay_return'),
    path('orden/confirmada/<int:orden_id>/', views.orden_confirmada, name='orden_confirmada'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('procesar-pago/', views.procesar_pago_view, name='procesar_pago'),
    path('orden-confirmada/', views.orden_confirmada_view, name='orden_confirmada'),
    path('limpiar-sesion/', views.limpiar_sesion_view, name='limpiar_sesion'),
    path('webpay/retorno/', views.webpay_retorno_view, name='webpay_retorno'),
    
    # Perfil y gestión de usuario
    path('perfil/', views.perfil_usuario_view, name='perfil'),
    path('mis-ordenes/', views.mis_ordenes_view, name='mis_ordenes'),
    path('logout/', LogoutView.as_view(next_page='home'), name='logout'),
    path('actualizar-imagen-perfil/', views.actualizar_imagen_perfil, name='actualizar_imagen_perfil'),
    path('toggle-veterinario/', views.toggle_veterinario, name='toggle_veterinario'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),

    # Veterinarios
    path('veterinario/perfil/', PerfilVeterinarioView.as_view(), name='perfil_veterinario'),
    path('veterinario/disponibilidad/', DisponibilidadVeterinarioView.as_view(), name='disponibilidad_veterinario'),
    path('veterinario/servicios/', ServiciosVeterinarioView.as_view(), name='servicios_veterinario'),
    path('veterinario/resenas/', ResenasVeterinarioView.as_view(), name='resenas_veterinario'),
    path('veterinario/servicios/<int:pk>/edit/', views.ServicioEditView.as_view(), name='servicio_edit'),
    path('veterinario/servicios/<int:pk>/delete/', ServicioDeleteView.as_view(), name='servicio_delete'),
    path('veterinario/servicios/toggle-estado/', ServicioToggleEstadoView.as_view(), name='servicio_toggle_estado'),

    # APIs de veterinario
    path('api/disponibilidad/', views.DisponibilidadAPIView.as_view(), name='api_disponibilidad'),
    path('api/disponibilidad/<int:pk>/', DisponibilidadDetailAPIView.as_view(), name='api_disponibilidad_detail'),
    path('api/disponibilidad/clonar/', DisponibilidadClonarAPIView.as_view(), name='api_disponibilidad_clonar'),
    path('api/disponibilidad/eventos/', DisponibilidadEventosAPIView.as_view(), name='api_disponibilidad_eventos'),

    # APIs de servicios
    path('api/servicios/', ServicioView.as_view(), name='servicios_api'),
    path('api/servicios/personalizado/', ServicioPersonalizadoView.as_view(), name='servicio_personalizado_api'),
    path('api/servicios/gestion/', GestionServiciosAPIView.as_view(), name='gestion_servicios_api'),
    path('servicios/gestion/', GestionServiciosView.as_view(), name='gestion_servicios'),

    path('veterinarios/', views.lista_veterinarios, name='lista_veterinarios'),
    path('api/veterinarios/filtrar/', views.filtrar_veterinarios, name='filtrar_veterinarios'),
    path('api/veterinario/actualizar-imagen/', VeterinarioImagenUpdateView.as_view(), name='api_veterinario_actualizar_imagen'),
    path('veterinario/perfil/actualizar/', VeterinarioPerfilUpdateView.as_view(), name='actualizar_perfil_veterinario'),
    path('api/veterinario/toggle/', views.toggle_veterinario, name='toggle_veterinario'),
    path('veterinarios/<int:veterinario_id>/', views.detalle_veterinario, name='detalle_veterinario'),
    path('veterinarios/<int:veterinario_id>/calificar/', views.calificar_veterinario, name='calificar_veterinario'),
    path('api/horarios-disponibles/', views.obtener_horarios_disponibles, name='horarios_disponibles'),
    path('api/citas/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),

    # URLs para citas veterinarias
    path('citas/agendar/', views.agendar_cita, name='agendar_cita'),
    path('citas/mis-citas/', views.mis_citas, name='mis_citas'),
    path('citas/<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

