# Módulos estándar
import json
import uuid
import random
import logging
from datetime import datetime, timedelta, date, time

# Django
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import path, reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers import serialize
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.db.models import Q, Avg, Count
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, FormView
from django.views.decorators.http import require_http_methods, require_POST

from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator

import json
from datetime import datetime

from django.contrib.auth import update_session_auth_hash

# Transbank
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.error.transbank_error import TransbankError

# Configuración de Django
from django.conf import settings

# Importaciones locales
from .models import (
    Producto, 
    CustomUser, 
    Orden, 
    OrdenItem,
    PerfilVeterinario,
    ServicioBase,
    ServicioPersonalizado,
    DisponibilidadVeterinario,
    validate_image_file_extension,  # Importar la función de validación
)
from .forms import (
    ProductoForm, 
    RegistroUsuarioForm, 
    CustomLoginForm, 
)

from PIL import Image  # Añade este import al inicio del archivo

logger = logging.getLogger(__name__)

# Aqui van las famosas vistas, no confundir
def home_view(request):
    return render(request, 'home.html')

def pago_view(request):
    return render(request,'pago/checkout.html')

#------------Carrito 
def agregar_al_carrito(request, sku):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
        
    try:
        producto = get_object_or_404(Producto, SKUProducto=sku)
        
        # Obtener carrito actual
        carrito = json.loads(request.COOKIES.get('carrito', '{}'))
        
        # Verificar stock
        cantidad_actual = carrito.get(str(sku), {}).get('cantidad', 0)
        if cantidad_actual + 1 > producto.StockProducto:
            return JsonResponse({
                'success': False, 
                'error': 'No hay suficiente stock disponible'
            })
        
        # Actualizar carrito
        if str(sku) in carrito:
            carrito[str(sku)]['cantidad'] += 1
        else:
            precio = float(producto.PrecioOferta if producto.EstaOferta else producto.PrecioProducto)
            carrito[str(sku)] = {
                'nombre': producto.NombreProducto,
                'precio': precio,
                'cantidad': 1,
                'descripcion': producto.DescripcionProducto,
                'imagen': producto.ImagenProducto.url if producto.ImagenProducto else None,
            }
        
        # Crear respuesta JSON
        response = JsonResponse({
            'success': True,
            'cart_count': sum(item['cantidad'] for item in carrito.values()),
            'message': 'Producto agregado al carrito'
        })
        
        # Actualizar cookie
        response.set_cookie('carrito', json.dumps(carrito))
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

# Ver el carrito
def carrito_view(request):
    # Obtener carrito desde cookies
    carrito = request.COOKIES.get('carrito', '{}')
    try:
        carrito = json.loads(carrito)
    except json.JSONDecodeError:
        carrito = {}
    
    # Obtener información completa de los productos en el carrito
    for sku, item in carrito.items():
        producto = Producto.objects.get(SKUProducto=sku)
        carrito[sku].update({
            'imagen': producto.ImagenProducto.url if producto.ImagenProducto else None,
            'descripcion': producto.DescripcionProducto,
            'stock': producto.StockProducto,
            'precio': float(producto.PrecioOferta if producto.EstaOferta else producto.PrecioProducto)
        })
    
    # Cálculos del carrito
    subtotal = sum(float(item['precio']) * item['cantidad'] for item in carrito.values())
    shipping = 0 if subtotal >= 20000 else 3990
    total = subtotal + shipping

    context = {
        'carrito': carrito,
        'subtotal': subtotal,
        'shipping': shipping,
        'total': total,
    }

    return render(request, 'pago/carrito.html', context)

def actualizar_cantidad(request):
    if request.method == 'POST':
        sku = request.POST.get('item_id')
        cantidad = int(request.POST.get('quantity'))
        
        # Obtener carrito desde cookies
        carrito_str = request.COOKIES.get('carrito', '{}')
        try:
            carrito = json.loads(carrito_str)
        except json.JSONDecodeError:
            carrito = {}
        
        if str(sku) in carrito:
            # Verificar stock disponible
            producto = Producto.objects.get(SKUProducto=sku)
            cantidad = min(cantidad, producto.StockProducto)  # Limitar a stock disponible
            
            # Actualizar cantidad
            carrito[str(sku)]['cantidad'] = cantidad
            
            # Recalcular totales
            subtotal = sum(float(item['precio']) * int(item['cantidad']) 
                         for item in carrito.values())
            shipping = 0 if subtotal >= 20000 else 3990
            total = subtotal + shipping
            
            # Crear respuesta JSON
            response = JsonResponse({
                'status': 'ok',
                'subtotal': subtotal,
                'shipping': shipping,
                'total': total,
                'quantity': cantidad
            })
            
            # Actualizar cookie
            response.set_cookie('carrito', json.dumps(carrito))
            return response
    
    return JsonResponse({'status': 'error'}, status=400)

# Eliminar un producto del carrito
def eliminar_del_carrito(request, sku):
    # Obtener carrito desde cookies
    carrito_str = request.COOKIES.get('carrito', '{}')
    try:
        carrito = json.loads(carrito_str)
    except json.JSONDecodeError:
        carrito = {}

    if str(sku) in carrito:
        del carrito[str(sku)]
        response = redirect('carrito')
        response.set_cookie('carrito', json.dumps(carrito))
        return response

    return redirect('carrito')

# Limpiar el carrito
def limpiar_carrito(request):
    if request.method == 'POST':
        response = redirect('carrito')
        response.delete_cookie('carrito')
        messages.success(request, 'El carrito ha sido vaciado exitosamente')
        return response
    return redirect('carrito')
#------------Fin Carrito 

#------------Usuarios 
class RegistroUsuarioView(FormView):
    template_name = 'usuario/late_registration.html'
    form_class = RegistroUsuarioForm
    success_url = reverse_lazy('home') 

    def form_valid(self, form):
        if form.is_valid():
            print("Formulario válido")
            form.save()
            messages.success(self.request, '¡Tu cuenta ha sido creada exitosamente!')
        else:
            print("Formulario no es válido")
            messages.error(self.request, 'Por favor, revisa los datos.')
        return super().form_valid(form)

class CustomLoginView(LoginView):
    template_name = 'usuario/late_login.html'
    authentication_form = CustomLoginForm  # Usa el formulario personalizado
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('home')  # Redirige a la página de inicio después del login
    
@login_required
def perfil_usuario_view(request):
    if request.method == 'POST':
        user = request.user
        user.NombreUsuario = request.POST.get('nombre')
        user.ApellidoUsuario = request.POST.get('apellido')
        user.EmailUsuario = request.POST.get('email')
        
        # Manejar el teléfono
        telefono = request.POST.get('telefono', '')
        # Remover el prefijo si existe
        if telefono.startswith('+56'):
            telefono = telefono[3:]
        # Limpiar cualquier espacio o carácter no numérico
        telefono = ''.join(filter(str.isdigit, telefono))
        # Agregar el prefijo si no está vacío
        user.TelefonoUsuario = f'+56{telefono}' if telefono else None
        
        user.DomicilioUsuario = request.POST.get('direccion')
        
        # Manejar el tipo de animal
        tipo_animal = request.POST.get('tipo_animal')
        if tipo_animal:
            try:
                # Reemplazar la coma por punto y convertir a float
                tipo_animal = float(tipo_animal.replace(',', '.'))
                user.TipoAnimal = tipo_animal
            except ValueError:
                messages.error(request, 'Valor inválido para el tipo de animal')
                return redirect('perfil')
        else:
            user.TipoAnimal = None
        
        try:
            user.save()
            messages.success(request, 'Perfil actualizado correctamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
        
        return redirect('perfil')

    return render(request, 'usuario/perfil.html')
    
    
    

@login_required
def mis_ordenes_view(request):
    # Obtener todas las órdenes del usuario actual, ordenadas por fecha descendente
    ordenes = Orden.objects.filter(usuario=request.user).order_by('-FechaOrden')
    
    # Obtener filtros de la URL
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Aplicar filtros si existen
    if estado:
        ordenes = ordenes.filter(EstadoOrden=estado)
    if fecha_desde:
        ordenes = ordenes.filter(FechaOrden__gte=fecha_desde)
    if fecha_hasta:
        ordenes = ordenes.filter(FechaOrden__lte=fecha_hasta)
    
    context = {
        'ordenes': ordenes,
        'filtro_estado': estado,
        'filtro_fecha_desde': fecha_desde,
        'filtro_fecha_hasta': fecha_hasta
    }
    return render(request, 'usuario/mis_ordenes.html', context)
    
    
    

@login_required
def actualizar_imagen_perfil(request):
    if request.method == 'POST' and request.FILES.get('imagen'):
        imagen = request.FILES['imagen']
        
        # Validar extensión usando la función del modelo
        try:
            validate_image_file_extension(imagen)
        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
        
        # Actualizar imagen
        try:
            user = request.user
            user.ImagenPerfil = imagen
            user.save()
            
            return JsonResponse({
                'success': True,
                'image_url': user.ImagenPerfil.url
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al actualizar la imagen: {str(e)}'
            })
            
    return JsonResponse({
        'success': False,
        'error': 'No se proporcionó ninguna imagen'
    })

@login_required
@require_POST
def toggle_veterinario(request):
    """
    Vista para activar/desactivar el rol de veterinario de un usuario y su perfil asociado.
    Requiere autenticación y método POST.
    """
    try:
        data = json.loads(request.body)
        is_veterinario = data.get('is_veterinario')
        desactivar_perfil = data.get('desactivar_perfil', False)
        
        usuario = request.user
        usuario.is_veterinario = is_veterinario
        usuario.save()
        
        mensaje = "Tu estado de veterinario ha sido actualizado"
        
        # Si se está desactivando el rol de veterinario, desactivar también el perfil
        if desactivar_perfil:
            perfil_veterinario = get_object_or_404(PerfilVeterinario, usuario=usuario)
            perfil_veterinario.EstaActivo = False
            perfil_veterinario.save()
            mensaje = "Has dejado de ser veterinario y tu perfil ha sido desactivado"
        
        return JsonResponse({
            'success': True,
            'message': mensaje
        })
        
    except PerfilVeterinario.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Perfil veterinario no encontrado'
        }, status=404)
    except Exception as e:
        logger.error(f"Error en toggle_veterinario: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Error al procesar la solicitud'
        }, status=400)

@login_required
@require_POST
def cambiar_password(request):
    try:
        # Obtener los datos del formulario
        data = json.loads(request.body)
        password_actual = data.get('password_actual')
        password_nuevo = data.get('password_nuevo')
        password_confirmacion = data.get('password_confirmacion')

        # Verificar que todos los campos estén presentes
        if not all([password_actual, password_nuevo, password_confirmacion]):
            return JsonResponse({
                'success': False,
                'error': 'Todos los campos son requeridos'
            })

        # Verificar contraseña actual usando el método de AbstractBaseUser
        if not request.user.check_password(password_actual):
            return JsonResponse({
                'success': False,
                'error': 'La contraseña actual es incorrecta'
            })

        # Verificar que las contraseñas nuevas coincidan
        if password_nuevo != password_confirmacion:
            return JsonResponse({
                'success': False,
                'error': 'Las contraseñas nuevas no coinciden'
            })

        # Validar requisitos mínimos de la nueva contraseña
        if len(password_nuevo) < 8:
            return JsonResponse({
                'success': False,
                'error': 'La contraseña debe tener al menos 8 caracteres'
            })

        # Cambiar la contraseña
        request.user.set_password(password_nuevo)
        request.user.save()

        # Actualizar la sesión para que el usuario no sea desconectado
        update_session_auth_hash(request, request.user)

        return JsonResponse({
            'success': True,
            'message': 'Contraseña actualizada correctamente'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Datos inválidos'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
#-----------Fin de usuarios 


#----------------Catalogo 
def catalogo_view(request):
    # Carga inicial de todos los productos
    productos = Producto.objects.all()
    productos_oferta = Producto.objects.filter(EstaOferta=True)[:3]  # Limitamos a 3 productos en oferta

    # Obtener las opciones para los filtros
    categorias = Producto._meta.get_field('CategoriaProducto').choices
    tipos_animal = Producto._meta.get_field('TipoAnimal').choices

    # Aplicar filtros existentes
    query = request.GET.get('q')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    categoria = request.GET.get('categoria')
    tipo_animal = request.GET.get('tipo_animal')
    items_per_page_choices = [5, 10, 20, 50, 100, 200]
    items_per_page = int(request.GET.get('items_per_page', 20))  # 20 como valor por defecto

    if query:
        productos = productos.filter(NombreProducto__icontains=query)

    if min_price:
        try:
            min_price = float(min_price)
            productos = productos.filter(PrecioProducto__gte=min_price)
        except ValueError:
            pass

    if max_price:
        try:
            max_price = float(max_price)
            productos = productos.filter(PrecioProducto__lte=max_price)
        except ValueError:
            pass

    if categoria:
        productos = productos.filter(CategoriaProducto=categoria)

    if tipo_animal:
        productos = productos.filter(TipoAnimal=tipo_animal)

    # Paginación
    try:
        items_per_page = int(items_per_page)
    except ValueError:
        items_per_page = 12

    paginator = Paginator(productos, items_per_page)
    page = request.GET.get('page')
    
    try:
        productos_paginados = paginator.page(page)
    except PageNotAnInteger:
        productos_paginados = paginator.page(1)
    except EmptyPage:
        productos_paginados = paginator.page(paginator.num_pages)

    # Formatear precios para el carrusel
    for producto in productos_oferta:
        producto.PrecioProducto = int(producto.PrecioProducto)
        producto.PrecioOferta = int(producto.PrecioOferta) if producto.EstaOferta else producto.PrecioProducto
    
    context = {
        'productos': productos_paginados,
        'productos_oferta': productos_oferta,  # Añadimos los productos en oferta al contexto
        'categorias': categorias,
        'tipos_animal': tipos_animal,
        'items_per_page': items_per_page,
        'items_per_page_choices': items_per_page_choices,  # Añadimos las opciones al contexto
        'current_filters': {
            'q': query,
            'min_price': min_price,
            'max_price': max_price,
            'categoria': categoria,
            'tipo_animal': tipo_animal,
        }
    }

    return render(request, 'catalogo/product_list.html', context)


class Product_ListView(ListView):
    model = Producto
    template_name = 'catalogo/product_list.html'
    context_object_name = 'productos'

def buscar_producto_por_sku(sku):
    try:
        return Producto.objects.get(SKUProducto=sku)
    except Producto.DoesNotExist:
        return None

def producto_detalle_modal(request, sku):
    producto = get_object_or_404(Producto, SKUProducto=sku)

    producto_data = {
        'nombre': producto.NombreProducto,
        'descripcion': producto.DescripcionProducto,
        'precio': f"${producto.PrecioProducto:,.0f}",
        'precio_oferta': f"${producto.PrecioOferta:,.0f}" if producto.EstaOferta else None,
        'imagen_url': producto.ImagenProducto.url if producto.ImagenProducto else '',
        'stock': producto.StockProducto,
        'esta_en_oferta': producto.EstaOferta,
        'categoria': producto.get_CategoriaProducto_display(),
        'tipo_animal': producto.get_TipoAnimal_display(),
        
    }

    return JsonResponse(producto_data)
#----------------Fin Catalogo 

#----------------CRUD de Producto
class Product_CreateView(CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'catalogo/product_form.html'
    success_url = reverse_lazy('productos')
    paginate_by = 10

    def get_context_data(self, **kwargs):
        # Inicializamos el objeto
        self.object = None
        context = {}
        
        # Obtenemos el formulario
        context['form'] = kwargs.get('form', self.get_form())
        
        # Obtener parámetros de la URL
        search_query = self.request.GET.get('search', '')
        order_by = self.request.GET.get('order_by', '-SKUProducto')
        items_per_page = int(self.request.GET.get('items_per_page', 10))
        
        # Obtener productos con filtros
        productos = Producto.objects.all()
        
        # Aplicar búsqueda
        if search_query:
            productos = productos.filter(
                Q(NombreProducto__icontains=search_query) |
                Q(SKUProducto__icontains=search_query)
            )
        
        # Aplicar ordenamiento
        if order_by in ['SKUProducto', '-SKUProducto', 'NombreProducto', '-NombreProducto', 
                       'PrecioProducto', '-PrecioProducto', 'StockProducto', '-StockProducto']:
            productos = productos.order_by(order_by)
        
        # Paginación
        paginator = Paginator(productos, items_per_page)
        page = self.request.GET.get('page', 1)
        
        try:
            productos_paginados = paginator.page(page)
        except:
            productos_paginados = paginator.page(1)
        
        # Agregar parámetros al contexto
        context.update({
            'productos': productos_paginados,
            'search_query': search_query,
            'current_order': order_by,
            'items_per_page': items_per_page,
            'available_items_per_page': [5, 10, 25, 50, 100]
        })
        
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        sku = request.POST.get('SKUProducto')
        context = self.get_context_data(form=form)

        # Buscar
        if 'buscar' in request.POST and sku:
            producto = buscar_producto_por_sku(sku)
            if producto:
                form = self.form_class(instance=producto)
                messages.info(request, f'Producto encontrado: {producto.NombreProducto}')
            else:
                form = self.form_class(initial={'SKUProducto': sku})
                messages.warning(request, 'Producto no encontrado. Puede crear uno nuevo con este SKU.')
            context['form'] = form
            return render(request, self.template_name, context)

        # Crear o Actualizar
        elif 'crear_actualizar' in request.POST:
            producto = buscar_producto_por_sku(sku)
            if producto:
                # Si no se sube una nueva imagen, mantener la existente
                if not request.FILES.get('ImagenProducto'):
                    form = self.form_class(request.POST, instance=producto)
                else:
                    form = self.form_class(request.POST, request.FILES, instance=producto)
            else:
                form = self.form_class(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, 'Producto guardado exitosamente.')
                context['form'] = self.form_class()
            else:
                messages.error(request, 'Por favor corrija los errores en el formulario.')
            return render(request, self.template_name, context)

        # Borrar
        elif 'borrar' in request.POST and sku:
            producto = buscar_producto_por_sku(sku)
            if producto:
                nombre = producto.NombreProducto
                producto.delete()
                messages.success(request, f'Producto {nombre} eliminado exitosamente.')
                context['form'] = self.form_class()
            else:
                messages.error(request, 'No se encontró el producto.')
            return render(request, self.template_name, context)

        return render(request, self.template_name, context)
#----------------Fin CRUD de Producto

#----------------Checkout
def checkout_view(request):
    try:
        # Obtener carrito y calcular totales
        carrito = json.loads(request.COOKIES.get('carrito', '{}'))
        subtotal = sum(float(item['precio']) * item['cantidad'] for item in carrito.values())
        shipping = 0 if subtotal >= 20000 else 3990
        total = subtotal + shipping

        context = {
            'carrito': carrito,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
        }

        # Si el usuario está autenticado, agregar sus datos al contexto
        if request.user.is_authenticated:
            context['user'] = request.user

        return render(request, 'pago/checkout.html', context)

    except json.JSONDecodeError:
        messages.error(request, 'Error al procesar el carrito')
        return redirect('carrito')

def enviar_correo_confirmacion(orden):
    """Envía un correo de confirmación al cliente"""
    context = {
        'orden': orden,
        'logo_url': 'https://tutienda.com/static/img/logo.png',  # Actualiza con tu URL
        'seguimiento_url': f'https://tutienda.com/seguimiento/{orden.id}/',  # Actualiza con tu URL
    }
    
    # Renderizar el template HTML
    html_message = render_to_string('emails/confirmacion_orden.html', context)
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=f'Confirmación de Orden #{orden.id} - Tu Tienda',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[orden.EmailCliente],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Error enviando correo de confirmación: {str(e)}")
        return False

# Modificar la vista de webpay_return para incluir el envío del correo
def webpay_return(request):
    token = request.GET.get('token_ws')
    
    try:
        response = Transaction.commit(token=token)
        
        if response.status == 'AUTHORIZED':
            orden = Orden.objects.get(TokenWebpay=token)
            orden.EstadoPago = 'COMPLETADO'
            orden.save()
            
            # Enviar correo de confirmación
            enviar_correo_confirmacion(orden)
            
            # Limpiar carrito
            request.session['carrito'] = {}
            
            messages.success(request, '¡Pago realizado con éxito!')
            return redirect('orden_confirmada', orden_id=orden.CodigoUnicoOrden)
        else:
            messages.error(request, 'El pago no fue autorizado')
            return redirect('checkout')
            
    except TransbankError as e:
        messages.error(request, 'Error al procesar el pago: ' + str(e))
        return redirect('checkout')

def orden_confirmada(request, orden_id):
    try:
        orden = Orden.objects.get(CodigoUnicoOrden=orden_id)
        
        # Verificar que la orden pertenece al usuario actual
        if orden.RutUsuario != request.user.RutUsuario:
            messages.error(request, 'No tienes permiso para ver esta orden')
            return redirect('home')
        
        context = {
            'orden': orden,
            'fecha': orden.FechaOrden.strftime('%d/%m/%Y %H:%M'),
            'total': f"${orden.MontoTotal:,.0f}",
        }
        
        return render(request, 'pago/orden_confirmada.html', context)
        
    except Orden.DoesNotExist:
        messages.error(request, 'Orden no encontrada')
        return redirect('home')

def procesar_pago_view(request):
    if request.method != 'POST':
        logger.info("Método no es POST")
        return redirect('checkout')
    
    try:
        logger.info("Iniciando proceso de pago")
        
        # Validar datos del formulario
        campos_requeridos = ['rut', 'nombre', 'apellido', 'email', 'telefono', 'direccion']
        for campo in campos_requeridos:
            if not request.POST.get(campo):
                logger.error(f"Campo requerido faltante: {campo}")
                messages.error(request, f'El campo {campo} es requerido')
                return redirect('checkout')
        
        # Obtener datos del formulario
        datos_envio = {
            'rut': request.POST.get('rut'),
            'nombre': request.POST.get('nombre'),
            'apellido': request.POST.get('apellido'),
            'email': request.POST.get('email'),
            'telefono': request.POST.get('telefono'),
            'direccion': request.POST.get('direccion'),
        }
        
        logger.info(f"Datos de envío recibidos: {datos_envio}")
        
        # Obtener carrito
        carrito_str = request.COOKIES.get('carrito', '{}')
        carrito = json.loads(carrito_str)
        
        if not carrito:
            logger.error("Carrito vacío")
            messages.error(request, 'No hay productos en el carrito')
            return redirect('carrito')
        
        # Calcular totales
        subtotal = sum(float(item['precio']) * int(item['cantidad']) for item in carrito.values())
        shipping = 0 if subtotal >= 20000 else 3990
        total = subtotal + shipping
        
        logger.info(f"Total calculado: {total}")
        
        # Verificar stock antes de crear la orden
        for key, item in carrito.items():
            try:
                producto = Producto.objects.get(SKUProducto=key)
                if producto.StockProducto < int(item['cantidad']):
                    messages.error(request, f'Stock insuficiente para {producto.NombreProducto}')
                    return redirect('checkout')
            except Producto.DoesNotExist:
                messages.error(request, f'Producto no encontrado: {key}')
                return redirect('checkout')
        
        # Crear la orden
        try:
            orden = Orden.objects.create(
                NombreCliente=datos_envio['nombre'],
                ApellidoCliente=datos_envio['apellido'],
                EmailCliente=datos_envio['email'],
                TelefonoCliente=datos_envio['telefono'],
                DireccionCliente=datos_envio['direccion'],
                TotalOrden=total,
                CostoEnvio=shipping,
                EstadoOrden='pendiente'
            )
            logger.info(f"Orden creada con ID: {orden.id}")
            
            # Crear items de la orden
            for key, item in carrito.items():
                OrdenItem.objects.create(
                    orden=orden,
                    SKUProducto_id=key,
                    NombreProducto=item['nombre'],
                    PrecioProducto=item['precio'],
                    CantidadProducto=item['cantidad']
                )
        except Exception as e:
            logger.error(f"Error creando orden: {str(e)}")
            raise
        
        try:
            # Configurar WebPay
            tx = Transaction()
            
            # Crear sesión de pago
            buy_order = str(orden.id)
            session_id = str(random.randrange(1000000, 99999999))
            amount = int(total)
            return_url = request.build_absolute_uri(reverse('webpay_retorno'))
            
            logger.info(f"Intentando crear transacción WebPay: orden={buy_order}, monto={amount}")
            
            response = tx.create(
                buy_order=buy_order,
                session_id=session_id,
                amount=amount,
                return_url=return_url
            )
            
            logger.info(f"Respuesta de WebPay: {response}")
            
            # Guardar token en la orden
            orden.TokenWebpay = response['token']
            orden.save()
            
            # Guardar datos en sesión
            request.session['orden_id'] = orden.id
            
            # Redireccionar a WebPay
            webpay_url = response['url'] + '?token_ws=' + response['token']
            logger.info(f"Redirigiendo a WebPay: {webpay_url}")
            return redirect(webpay_url)
            
        except TransbankError as e:
            logger.error(f"Error de Transbank: {str(e)}")
            messages.error(request, 'Error al conectar con el servicio de pago')
            return redirect('checkout')
            
    except Exception as e:
        logger.error(f"Error procesando pago: {str(e)}")
        messages.error(request, 'Error al procesar el pago')
        return redirect('checkout')

def orden_confirmada_view(request):
    orden_id = request.session.get('orden_id')
    if not orden_id:
        return redirect('checkout')
    
    try:
        orden = Orden.objects.get(id=orden_id)
        subtotal = orden.TotalOrden - orden.CostoEnvio
        
        # Obtener el estado del envío de correo de la sesión
        correo_enviado = request.session.get('correo_enviado', False)
        
        context = {
            'orden': orden,
            'subtotal': subtotal,
            'correo_enviado': correo_enviado
        }
        
        return render(request, 'pago/orden_confirmada.html', context)
        
    except Orden.DoesNotExist:
        messages.error(request, 'Orden no encontrada')
        return redirect('checkout')

@require_POST
def limpiar_sesion_view(request):
    """
    Esta vista ya no limpiará todos los datos, solo los temporales
    que no necesitemos mantener después de la compra
    """
    # Mantener datos importantes
    datos_importantes = {
        'orden_id': request.session.get('orden_id'),
        'datos_envio': request.session.get('datos_envio'),
        'total_pedido': request.session.get('total_pedido')
    }
    
    # Limpiar solo datos temporales si los hubiera
    request.session.clear()
    
    # Restaurar datos importantes
    for key, value in datos_importantes.items():
        if value is not None:
            request.session[key] = value
    
    return JsonResponse({'status': 'ok'})

def webpay_retorno_view(request):
    token = request.GET.get('token_ws')
    
    if not token:
        messages.error(request, 'No se recibió token de WebPay')
        return redirect('checkout')
    
    try:
        tx = Transaction()
        response = tx.commit(token)
        
        try:
            orden = Orden.objects.get(TokenWebpay=token)
        except Orden.DoesNotExist:
            messages.error(request, 'Orden no encontrada')
            return redirect('checkout')
        
        if response['response_code'] == 0:  # Pago exitoso
            # Actualizar orden
            orden.EstadoOrden = 'pagado'
            
            # Descontar stock de los productos
            for item in orden.items.all():
                try:
                    producto = Producto.objects.get(SKUProducto=item.SKUProducto_id)
                    if producto.StockProducto >= item.CantidadProducto:
                        producto.StockProducto -= item.CantidadProducto
                        producto.save()
                    else:
                        logger.error(f"Stock insuficiente para producto {producto.SKUProducto}")
                        messages.warning(request, f'Stock insuficiente para {producto.NombreProducto}')
                except Producto.DoesNotExist:
                    logger.error(f"Producto no encontrado: {item.SKUProducto_id}")
                    continue
            
            orden.save()
            
            # Enviar correo de confirmación
            try:
                # Preparar contexto para el email
                context = {
                    'orden': orden,
                    'items': orden.items.all(),
                    'subtotal': orden.TotalOrden - orden.CostoEnvio,
                }
                
                # Renderizar el template HTML
                html_message = render_to_string('emails/confirmacion_orden.html', context)
                plain_message = strip_tags(html_message)
                
                # Enviar el correo
                send_mail(
                    subject=f'Confirmación de Orden #{orden.id} - PetShop',
                    message=plain_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[orden.EmailCliente],
                    html_message=html_message,
                    fail_silently=False,
                )
                
                logger.info(f"Correo de confirmación enviado para orden #{orden.id}")
                correo_enviado = True
                
            except Exception as e:
                logger.error(f"Error enviando correo de confirmación: {str(e)}")
                correo_enviado = False
            
            # Limpiar carrito y redireccionar
            response = redirect('orden_confirmada')
            response.delete_cookie('carrito')
            
            # Guardar el estado del envío de correo en la sesión
            request.session['correo_enviado'] = correo_enviado
            
            messages.success(request, '¡Pago procesado exitosamente!')
            return response
            
        else:
            # Pago rechazado
            orden.EstadoOrden = 'cancelado'
            orden.save()
            messages.error(request, 'El pago fue rechazado por WebPay')
            return redirect('checkout')
            
    except Exception as e:
        logger.error(f"Error en retorno WebPay: {str(e)}")
        messages.error(request, 'Error procesando el pago')
        return redirect('checkout')
#----------------Fin Checkout

@method_decorator(login_required, name='dispatch')
class PerfilVeterinarioView(LoginRequiredMixin, View):
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_veterinario:
            messages.warning(request, 'No tienes acceso al perfil veterinario')
            return redirect('home')
            
        # Crear perfil veterinario si no existe
        if not hasattr(request.user, 'perfil_veterinario'):
            PerfilVeterinario.objects.create(
                usuario=request.user,
                NombreCompletoVeterinario=f"{request.user.NombreUsuario} {request.user.ApellidoUsuario}",
                EmailVeterinario=request.user.EmailUsuario,
                TelefonoVeterinario=int(request.user.get_phone_without_prefix()) if request.user.TelefonoUsuario else None,
                Especialidad="General",  # Valor por defecto
                NumeroRegistro="Pendiente",  # Valor por defecto
                Descripcion="Por favor, actualiza tu descripción profesional.",
            )
            messages.success(request, 'Se ha creado tu perfil veterinario. Por favor, completa tu información.')
            
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        context = {
            'perfil': request.user.perfil_veterinario,
            'seccion': request.GET.get('seccion', None)
        }
        return render(request, 'veterinaria/perfil_veterinario.html', context)

    def post(self, request):
        if request.content_type == 'application/json':
            return self.handle_ajax(request)
        else:
            return self.handle_form(request)

    def handle_form(self, request):
        perfil = request.user.perfil_veterinario
        try:
            # Actualizar datos del perfil desde form
            perfil.NombreVeterinario = request.POST.get('nombre')
            perfil.ApellidoVeterinario = request.POST.get('apellido')
            perfil.EmailVeterinario = request.POST.get('email')
            perfil.Telefono = request.POST.get('telefono')
            perfil.Especialidad = request.POST.get('especialidad')
            perfil.NumeroRegistro = request.POST.get('numero_registro')
            perfil.Descripcion = request.POST.get('descripcion')
            perfil.save()
            
            messages.success(request, 'Perfil actualizado correctamente')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
        
        return redirect('perfil_veterinario')

    def handle_ajax(self, request):
        try:
            perfil = request.user.perfil_veterinario
            data = json.loads(request.body)
            accion = data.get('accion')
            
            if accion == 'actualizar_imagen':
                if 'imagen' in request.FILES:
                    imagen = request.FILES['imagen']
                    try:
                        validate_image_file_extension(imagen)
                        perfil.ImagenPerfil = imagen
                        perfil.save()
                        return JsonResponse({
                            'success': True,
                            'imagen_url': perfil.ImagenPerfil.url
                        })
                    except ValidationError as e:
                        return JsonResponse({'error': str(e)}, status=400)
                return JsonResponse({'error': 'No se proporcionó imagen'}, status=400)
            
            elif accion == 'actualizar_perfil':
                campos_permitidos = [
                    'NombreVeterinario', 'ApellidoVeterinario', 'EmailVeterinario',
                    'Telefono', 'Especialidad', 'NumeroRegistro', 'Descripcion'
                ]
                
                for campo in campos_permitidos:
                    if campo in data:
                        setattr(perfil, campo, data[campo])
                
                perfil.save()
                return JsonResponse({'success': True})
            
            return JsonResponse({'error': 'Acción no válida'}, status=400)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(login_required, name='dispatch')
class ServiciosVeterinarioView(View):
    def get(self, request):
        if not request.user.is_veterinario:
            messages.warning(request, 'No tienes acceso al perfil veterinario')
            return redirect('home')
            
        try:
            perfil = request.user.perfil_veterinario
            servicios_personalizados = ServicioPersonalizado.objects.filter(
                veterinario=perfil
            )
            servicios_base_disponibles = ServicioBase.objects.exclude(
                CodigoServicio__in=servicios_personalizados.values_list('servicio_base__CodigoServicio', flat=True)
            )
            
            context = {
                'perfil': perfil,
                'servicios_personalizados': servicios_personalizados,
                'servicios_base_disponibles': servicios_base_disponibles,
                'seccion': 'servicios'
            }
            
            return render(request, 'veterinaria/perfil_veterinario.html', context)
            
        except Exception as e:
            messages.error(request, f'Error al cargar los servicios: {str(e)}')
            return redirect('perfil_veterinario')

@method_decorator(login_required, name='dispatch')
class ServicioDeleteView(View):
    def post(self, request, pk):
        if not request.user.is_staff:
            return JsonResponse({
                'error': 'No tienes permisos para realizar esta acción'
            }, status=403)
            
        try:
            servicio = get_object_or_404(ServicioBase, CodigoServicio=pk)
            
            # Eliminar primero los servicios personalizados asociados
            ServicioPersonalizado.objects.filter(servicio_base=servicio).delete()
                
            # Luego eliminar el servicio base
            servicio.delete()
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=400)

@method_decorator(login_required, name='dispatch')
class PrecioPersonalizadoView(View):
    def post(self, request):
        if not request.user.is_veterinario:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para realizar esta acción'
            }, status=403)
        
        perfil = get_object_or_404(PerfilVeterinario, usuario=request.user)
        servicio_id = request.POST.get('servicio')
        precio = request.POST.get('precio')
        
        try:
            precio_personalizado, created = PrecioPersonalizado.objects.update_or_create(
                veterinario=perfil,
                servicio_id=servicio_id,
                defaults={'Precio': precio}
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Precio actualizado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class DisponibilidadVeterinarioView(LoginRequiredMixin, View):
    def get(self, request):
        if not hasattr(request.user, 'perfil_veterinario'):
            return redirect('perfil_usuario')
        
        context = {
            'perfil': request.user.perfil_veterinario,
            'seccion': 'disponibilidad'
        }
        return render(request, 'veterinaria/perfil_veterinario.html', context)

class DisponibilidadAPIView(LoginRequiredMixin, View):
    def get(self, request):
        """Obtener disponibilidades por fecha"""
        fecha = request.GET.get('fecha')
        if not fecha:
            return JsonResponse({'error': 'Fecha requerida'}, status=400)

        disponibilidades = DisponibilidadVeterinario.objects.filter(
            veterinario=request.user.perfil_veterinario,
            Fecha=fecha
        ).values('id', 'HorarioInicio', 'HorarioFin', 'EstaDisponible')

        return JsonResponse(list(disponibilidades), safe=False)

    def post(self, request):
        """Crear nueva disponibilidad"""
        try:
            data = json.loads(request.body)
            fecha = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
            horario_inicio = datetime.strptime(data['horario_inicio'], '%H:%M').time()
            horario_fin = datetime.strptime(data['horario_fin'], '%H:%M').time()

            # Verificar si ya existe un horario que se solape
            if DisponibilidadVeterinario.objects.filter(
                veterinario=request.user.perfil_veterinario,
                Fecha=fecha,
                HorarioInicio__lt=horario_fin,
                HorarioFin__gt=horario_inicio
            ).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Ya existe un horario que se solapa con el ingresado'
                }, status=400)

            DisponibilidadVeterinario.objects.create(
                veterinario=request.user.perfil_veterinario,
                Fecha=fecha,
                HorarioInicio=horario_inicio,
                HorarioFin=horario_fin
            )

            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class DisponibilidadDetailAPIView(LoginRequiredMixin, View):
    def put(self, request, pk):
        """Actualizar disponibilidad existente"""
        if not request.user.is_veterinario:
            return JsonResponse({'error': 'No autorizado'}, status=403)

        try:
            disponibilidad = get_object_or_404(
                DisponibilidadVeterinario, 
                id=pk, 
                veterinario__usuario=request.user
            )
            data = json.loads(request.body)

            # Actualizar campos
            if 'horario_inicio' in data:
                disponibilidad.HorarioInicio = datetime.strptime(
                    data['horario_inicio'], '%H:%M'
                ).time()
            if 'horario_fin' in data:
                disponibilidad.HorarioFin = datetime.strptime(
                    data['horario_fin'], '%H:%M'
                ).time()
            if 'esta_disponible' in data:
                disponibilidad.EstaDisponible = data['esta_disponible']

            disponibilidad.save()

            return JsonResponse({
                'success': True,
                'message': 'Disponibilidad actualizada exitosamente'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

    def delete(self, request, pk):
        """Eliminar disponibilidad"""
        if not request.user.is_veterinario:
            return JsonResponse({'error': 'No autorizado'}, status=403)

        try:
            disponibilidad = get_object_or_404(
                DisponibilidadVeterinario, 
                id=pk, 
                veterinario__usuario=request.user
            )
            disponibilidad.delete()

            return JsonResponse({
                'success': True,
                'message': 'Disponibilidad eliminada exitosamente'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

class DisponibilidadClonarAPIView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            horario_original = get_object_or_404(
                DisponibilidadVeterinario, 
                id=data['horario_id'],
                veterinario__usuario=request.user
            )
            
            tipo_clon = data['tipo_clon']
            fechas_destino = []
            
            if tipo_clon == 'siguiente':
                fecha = horario_original.Fecha + timedelta(days=1)
                fechas_destino = [fecha]
            elif tipo_clon == 'semana':
                fecha_base = horario_original.Fecha
                fechas_destino = [
                    fecha_base + timedelta(days=i) 
                    for i in range(1, 8)
                ]
            elif tipo_clon == 'especifico':
                fechas_destino = [datetime.strptime(data['fecha_destino'], '%Y-%m-%d').date()]
            
            for fecha in fechas_destino:
                DisponibilidadVeterinario.objects.create(
                    veterinario=horario_original.veterinario,
                    Fecha=fecha,
                    HorarioInicio=horario_original.HorarioInicio,
                    HorarioFin=horario_original.HorarioFin
                )
            
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

class DisponibilidadEventosAPIView(LoginRequiredMixin, View):
    def get(self, request):
        start = request.GET.get('start')
        end = request.GET.get('end')
        
        disponibilidades = DisponibilidadVeterinario.objects.filter(
            veterinario=request.user.perfil_veterinario,
            Fecha__range=[start[:10], end[:10]]  # Tomamos solo la fecha YYYY-MM-DD
        )
        
        eventos = []
        for disp in disponibilidades:
            eventos.append({
                'id': disp.id,
                'title': f'{disp.HorarioInicio.strftime("%H:%M")} - {disp.HorarioFin.strftime("%H:%M")}',
                'start': disp.Fecha.isoformat(),
                'display': 'background'
            })
        
        return JsonResponse(eventos, safe=False)

@method_decorator(login_required, name='dispatch')
class ServicioView(View):
    def get(self, request):
        # Todos pueden ver los servicios
        servicios = ServicioBase.objects.all()
        return JsonResponse({
            'servicios': list(servicios.values())
        })

    def post(self, request):
        # Solo staff puede crear/editar servicios base
        if not request.user.is_staff:
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        try:
            data = json.loads(request.body)
            servicio = ServicioBase.objects.create(
                NombreServicio=data['nombre'],
                Descripcion=data['descripcion'],
                TipoServicio=data['tipo'],
                DuracionEstimada=data['duracion'],
                EstaActivo=True
            )
            return JsonResponse({
                'success': True,
                'servicio': {
                    'id': servicio.CodigoServicio,
                    'nombre': servicio.NombreServicio,
                    'tipo': servicio.get_TipoServicio_display()
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

@method_decorator(login_required, name='dispatch')
class ServicioPersonalizadoView(View):
    def post(self, request):
        if not request.user.is_veterinario:
            return JsonResponse({'error': 'No autorizado'}, status=403)
        
        try:
            data = json.loads(request.body)
            perfil = request.user.perfil_veterinario
            accion = data.get('accion')
            
            if accion == 'eliminar':
                servicio_id = data.get('servicio_id')
                try:
                    servicio = ServicioPersonalizado.objects.get(
                        veterinario=perfil,
                        servicio_base__CodigoServicio=servicio_id
                    )
                    servicio.delete()
                    return JsonResponse({
                        'success': True,
                        'mensaje': 'Servicio eliminado correctamente'
                    })
                except ServicioPersonalizado.DoesNotExist:
                    return JsonResponse({
                        'error': 'Servicio no encontrado'
                    }, status=404)
            
            elif accion == 'agregar_multiples':
                servicios = data.get('servicios', [])
                
                for servicio_data in servicios:
                    servicio_base = ServicioBase.objects.get(
                        CodigoServicio=servicio_data['servicio_id']
                    )
                    
                    ServicioPersonalizado.objects.update_or_create(
                        veterinario=perfil,
                        servicio_base=servicio_base,
                        defaults={
                            'Precio': servicio_data['precio'],
                            'EstaActivo': servicio_data.get('esta_activo', True),
                            'Notas': servicio_data.get('notas', '')
                        }
                    )
                
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Servicios actualizados correctamente'
                })
            
            elif accion == 'toggle_estado':
                servicio_id = data.get('servicio_id')
                nuevo_estado = data.get('estado')
                
                servicio = get_object_or_404(
                    ServicioPersonalizado,
                    veterinario=perfil,
                    servicio_base__CodigoServicio=servicio_id
                )
                
                # Verificar si el servicio base está activo
                if nuevo_estado and not servicio.servicio_base.EstaActivo:
                    return JsonResponse({
                        'success': False,
                        'error': 'No se puede activar el servicio porque el servicio base está desactivado'
                    }, status=400)
                
                servicio.EstaActivo = nuevo_estado
                servicio.save()
                
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Estado actualizado correctamente'
                })
            
            else:  # Caso de un solo servicio
                servicio_base = ServicioBase.objects.get(
                    CodigoServicio=data['servicio_id']
                )
                
                ServicioPersonalizado.objects.update_or_create(
                    veterinario=perfil,
                    servicio_base=servicio_base,
                    defaults={
                        'Precio': data['precio'],
                        'EstaActivo': data.get('esta_activo', True),
                        'Notas': data.get('notas', '')
                    }
                )
                
                return JsonResponse({
                    'success': True,
                    'mensaje': 'Servicio actualizado correctamente'
                })
                
        except ServicioPersonalizado.DoesNotExist:
            return JsonResponse({
                'error': 'Servicio no encontrado'
            }, status=404)
        except (KeyError, ValueError) as e:
            return JsonResponse({
                'error': f'Datos inválidos: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'error': f'Error al procesar la solicitud: {str(e)}'
            }, status=500)


class GestionServiciosView(UserPassesTestMixin, TemplateView):
    template_name = 'veterinaria/gestion_servicios.html'
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener parámetros de ordenamiento
        order_by = self.request.GET.get('order_by', 'CodigoServicio')
        order_dir = self.request.GET.get('dir', 'asc')

        # Validar campo de ordenamiento
        valid_fields = ['CodigoServicio', 'NombreServicio', 'TipoServicio', 'EstaActivo']
        if order_by not in valid_fields:
            order_by = 'CodigoServicio'

        # Construir el ordenamiento
        order_string = f"{'-' if order_dir == 'desc' else ''}{order_by}"
        
        # Obtener servicios ordenados
        context['servicios'] = ServicioBase.objects.all().order_by(order_string)
        context['tipos_servicio'] = ServicioBase.TIPO_CHOICES
        context['order_by'] = order_by
        context['order_dir'] = order_dir
        return context

class GestionServiciosAPIView(UserPassesTestMixin, View):
    def test_func(self):
        return self.request.user.is_staff

    def get(self, request):
        servicio_id = request.GET.get('id')
        if servicio_id:
            servicio = get_object_or_404(ServicioBase, CodigoServicio=servicio_id)
            return JsonResponse({
                'servicio': {
                    'id': servicio.CodigoServicio,
                    'nombre': servicio.NombreServicio,
                    'tipo': servicio.TipoServicio,
                }
            })
        return JsonResponse({'error': 'ID de servicio no proporcionado'}, status=400)
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            accion = data.get('accion')
            
            if accion == 'crear':
                servicio = ServicioBase.objects.create(
                    NombreServicio=data['nombre'],
                    TipoServicio=data['tipo'],
                    EstaActivo=True
                )
                return JsonResponse({
                    'success': True,
                    'servicio': {
                        'id': servicio.CodigoServicio,
                        'nombre': servicio.NombreServicio,
                        'tipo': servicio.get_TipoServicio_display()
                    }
                })
                
            elif accion == 'editar':
                servicio = ServicioBase.objects.get(CodigoServicio=data['servicio_id'])
                servicio.NombreServicio = data['nombre']
                servicio.TipoServicio = data['tipo']
                servicio.save()
                return JsonResponse({'success': True})
                
            elif accion == 'toggle_estado':
                servicio = ServicioBase.objects.get(CodigoServicio=data['servicio_id'])
                servicio.EstaActivo = data['estado']
                servicio.save()
                return JsonResponse({'success': True})
                
            return JsonResponse({'error': 'Acción no válida'}, status=400)
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

def lista_veterinarios(request):
    # Obtener todos los veterinarios activos con sus calificaciones
    veterinarios = PerfilVeterinario.objects.filter(EstaActivo=True).annotate(
        promedio_rating=Avg('resenas__Calificacion'),
        total_reviews=Count('resenas'),
    )

    # Obtener lista única de especialidades
    especialidades = PerfilVeterinario.objects.values_list(
        'Especialidad', flat=True).distinct()

    context = {
        'veterinarios': veterinarios,
        'especialidades': especialidades,
    }
    
    return render(request, 'veterinaria/veterinarios_lista.html', context)

def filtrar_veterinarios(request):
    query = request.GET.get('query', '')
    tipo_atencion = request.GET.get('tipo_atencion', '')
    especialidad = request.GET.get('especialidad', '')

    # Iniciar con todos los veterinarios activos
    veterinarios = PerfilVeterinario.objects.filter(EstaActivo=True)

    # Aplicar filtros
    if query:
        veterinarios = veterinarios.filter(
            NombreVeterinario__icontains=query
        )

    if especialidad:
        veterinarios = veterinarios.filter(
            Especialidad__iexact=especialidad
        )

    if tipo_atencion:
        servicios_tipo = ServicioPersonalizado.objects.filter(
            servicio_base__TipoServicio=tipo_atencion,
            EstaActivo=True
        ).values_list('veterinario_id', flat=True)
        veterinarios = veterinarios.filter(id__in=servicios_tipo)

    # Agregar anotaciones para ratings
    veterinarios = veterinarios.annotate(
        promedio_rating=Avg('resenas__Calificacion'),
        total_reviews=Count('resenas')
    )

    # Preparar datos para JSON
    veterinarios_data = []
    for vet in veterinarios:
        servicios = ServicioPersonalizado.objects.filter(
            veterinario=vet,
            EstaActivo=True
        ).select_related('servicio_base')

        veterinarios_data.append({
            'id': vet.id,
            'nombre': vet.NombreVeterinario,
            'especialidad': vet.Especialidad,
            'imagen_url': vet.ImagenPerfil.url if vet.ImagenPerfil else None,
            'ubicacion': vet.Ubicacion,
            'promedio_rating': float(vet.promedio_rating) if vet.promedio_rating else 0,
            'total_reviews': vet.total_reviews,
            'servicios': [
                {
                    'nombre': s.servicio_base.NombreServicio,
                    'tipo': s.servicio_base.TipoServicio,
                    'precio': float(s.Precio)
                } for s in servicios
            ]
        })

    return JsonResponse({'veterinarios': veterinarios_data})

class VeterinarioPerfilUpdateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            perfil = request.user.perfil_veterinario
            
            # Actualizar campos existentes
            perfil.NombreCompletoVeterinario = request.POST.get('nombre_completo')
            perfil.EmailVeterinario = request.POST.get('email')
            perfil.TelefonoVeterinario = request.POST.get('telefono')
            perfil.Especialidad = request.POST.get('especialidad')
            perfil.NumeroRegistro = request.POST.get('numero_registro')
            perfil.Ubicacion = request.POST.get('ubicacion')
            perfil.MostrarUbicacion = request.POST.get('mostrar_ubicacion') == 'on'
            perfil.Descripcion = request.POST.get('descripcion')
            
            # Manejar el estado activo
            perfil.EstaActivo = request.POST.get('esta_activo') == 'on'
            
            perfil.save()
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Perfil actualizado correctamente',
                    'esta_activo': perfil.EstaActivo
                })
            
            messages.success(request, 'Perfil actualizado correctamente')
            return redirect('perfil_veterinario')
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
            
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
            return redirect('perfil_veterinario')

class VeterinarioImagenUpdateView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        try:
            if not hasattr(request.user, 'perfil_veterinario'):
                return JsonResponse({
                    'success': False,
                    'error': 'No se encontró el perfil veterinario'
                }, status=404)

            perfil = request.user.perfil_veterinario
            imagen = request.FILES.get('imagen_perfil')

            if not imagen:
                raise ValidationError('No se proporcionó ninguna imagen')

            # Validar tipo de archivo
            if not imagen.content_type.lower() in ['image/jpeg', 'image/png', 'image/webp']:
                raise ValidationError('Formato de imagen no soportado')

            # Validar tamaño (5MB máximo)
            if imagen.size > 5 * 1024 * 1024:
                raise ValidationError('La imagen no debe superar los 5MB')

            # Validar dimensiones
            try:
                img = Image.open(imagen)
                width, height = img.size
                if width < 200 or height < 200:
                    raise ValidationError('La imagen debe ser al menos de 200x200 píxeles')
            except Exception as e:
                raise ValidationError('Error al procesar la imagen')

            # Procesar y guardar imagen
            try:
                # Si ya existe una imagen, eliminarla
                if perfil.ImagenPerfil:
                    perfil.ImagenPerfil.delete(save=False)

                # Guardar nueva imagen
                perfil.ImagenPerfil = imagen
                perfil.save()

                return JsonResponse({
                    'success': True,
                    'message': 'Imagen actualizada correctamente',
                    'image_url': perfil.ImagenPerfil.url
                })

            except Exception as e:
                raise ValidationError('Error al procesar la imagen')

        except ValidationError as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'Error al actualizar la imagen'
            }, status=500)

class ResenasVeterinarioView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_veterinario:
            messages.warning(request, 'No tienes acceso al perfil veterinario')
            return redirect('home')
            
        # Corregir el nombre del campo para ordenar
        resenas = request.user.perfil_veterinario.resenas.all().order_by('-FechaCreacion')  # Cambiado de FechaResena a FechaCreacion
        
        # Calcular estadísticas
        promedio_calificacion = resenas.aggregate(Avg('Calificacion'))['Calificacion__avg'] or 0
        total_resenas = resenas.count()
        
        # Contar reseñas por calificación
        distribucion_calificaciones = {
            5: resenas.filter(Calificacion=5).count(),
            4: resenas.filter(Calificacion=4).count(),
            3: resenas.filter(Calificacion=3).count(),
            2: resenas.filter(Calificacion=2).count(),
            1: resenas.filter(Calificacion=1).count(),
        }
        
        context = {
            'perfil': request.user.perfil_veterinario,
            'seccion': 'resenas',
            'resenas': resenas,
            'promedio_calificacion': round(promedio_calificacion, 1),
            'total_resenas': total_resenas,
            'distribucion_calificaciones': distribucion_calificaciones,
        }
        
        return render(request, 'veterinaria/perfil_veterinario.html', context)

@method_decorator(login_required, name='dispatch')
class ServicioEditView(View):
    def post(self, request, pk):
        if not request.user.is_veterinario:
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para realizar esta acción'
            }, status=403)
            
        try:
            precio_personalizado = get_object_or_404(
                PrecioPersonalizado, 
                id=pk, 
                veterinario=request.user.perfil_veterinario
            )
            
            nuevo_precio = request.POST.get('precio')
            if not nuevo_precio:
                return JsonResponse({
                    'success': False,
                    'error': 'El precio es requerido'
                }, status=400)
                
            precio_personalizado.Precio = nuevo_precio
            precio_personalizado.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Precio actualizado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)

@method_decorator(login_required, name='dispatch')
class ServicioToggleEstadoView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_staff:
            messages.warning(request, 'No tienes permisos para realizar esta acción')
            return JsonResponse({
                'success': False,
                'error': 'No tienes permisos para realizar esta acción'
            }, status=403)
            
        try:
            data = json.loads(request.body)
            servicio_id = data.get('servicio_id')
            nuevo_estado = data.get('estado')

            if not servicio_id:
                return JsonResponse({
                    'success': False,
                    'error': 'ID de servicio no proporcionado'
                }, status=400)

            servicio_base = get_object_or_404(ServicioBase, CodigoServicio=servicio_id)
            
            # Actualizar estado del servicio base
            servicio_base.EstaActivo = nuevo_estado
            servicio_base.save()

            # Si se está deshabilitando, deshabilitar servicios personalizados
            servicios_afectados = 0
            if not nuevo_estado:
                servicios_personalizados = ServicioPersonalizado.objects.filter(
                    servicio_base=servicio_base
                )
                servicios_afectados = servicios_personalizados.count()
                servicios_personalizados.update(EstaActivo=False)
                
                logger.info(
                    f"Servicio {servicio_base.NombreServicio} (ID: {servicio_id}) " 
                    f"deshabilitado junto con {servicios_afectados} servicios personalizados"
                )
            else:
                logger.info(
                    f"Servicio {servicio_base.NombreServicio} (ID: {servicio_id}) habilitado"
                )

            mensaje = (
                f"Servicio '{servicio_base.NombreServicio}' deshabilitado y desactivado para {servicios_afectados} veterinarios"
                if not nuevo_estado else
                f"Servicio '{servicio_base.NombreServicio}' habilitado correctamente"
            )

            return JsonResponse({
                'success': True,
                'message': mensaje,
                'servicios_afectados': servicios_afectados
            })

        except json.JSONDecodeError:
            logger.error("Error decodificando JSON en ServicioToggleEstadoView")
            return JsonResponse({
                'success': False,
                'error': 'Datos inválidos'
            }, status=400)
            
        except ServicioBase.DoesNotExist:
            logger.warning(f"Intento de toggle en servicio inexistente ID: {servicio_id}")
            return JsonResponse({
                'success': False,
                'error': 'Servicio no encontrado'
            }, status=404)
            
        except Exception as e:
            logger.error(f"Error en ServicioToggleEstadoView: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Error al actualizar el estado del servicio'
            }, status=500)

