# Módulos estándar
import json
import uuid
import random
import logging
from datetime import datetime, timedelta, date

# Django
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.urls import path, reverse_lazy, reverse
from django.contrib import messages
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.core.serializers import serialize
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from django.db.models import Q
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, FormView
from django.views.decorators.http import require_http_methods, require_POST



# Transbank
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.error.transbank_error import TransbankError

# Configuración de Django
from django.conf import settings

# Importaciones locales
from .models import (
    Producto, 
    CustomUser, 
    Veterinaria, 
    Veterinario, 
    Servicio, 
    CitaVeterinaria, 
    Orden, 
    OrdenItem,
    validate_image_file_extension  # Importar la función de validación
)
from .forms import (
    ProductoForm, 
    RegistroUsuarioForm, 
    CustomLoginForm, 
    VeterinariaForm, 
    VeterinarioForm, 
    ServicioForm, 
    CitaVeterinariaForm
)


logger = logging.getLogger(__name__)

# Aqui van las famosas vistas, no confundir
def home_view(request):
    return render(request, 'home.html')

def pago_view(request):
    return render(request,'pago/checkout.html')

#------------Carrito 
def agregar_al_carrito(request, sku):
    producto = get_object_or_404(Producto, SKUProducto=sku)
    
    # Obtener carrito actual de las cookies
    carrito = request.COOKIES.get('carrito', '{}')
    try:
        carrito = json.loads(carrito)
    except json.JSONDecodeError:
        carrito = {}
    
    # Verificar stock antes de agregar
    cantidad_actual = carrito.get(str(sku), {}).get('cantidad', 0)
    if cantidad_actual + 1 > producto.StockProducto:
        messages.warning(request, 'No hay suficiente stock disponible')
        return redirect('carrito')
    
    if str(producto.SKUProducto) in carrito:
        carrito[str(producto.SKUProducto)]['cantidad'] += 1
    else:
        precio = float(producto.PrecioOferta if producto.EstaOferta else producto.PrecioProducto)
        carrito[str(producto.SKUProducto)] = {
            'nombre': producto.NombreProducto,
            'precio': precio,
            'cantidad': 1,
            'descripcion': producto.DescripcionProducto,
            'imagen': producto.ImagenProducto.url if producto.ImagenProducto else None,
        }

    # Crear la respuesta y establecer la cookie
    response = redirect('carrito')
    response.set_cookie('carrito', json.dumps(carrito))
    return response

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
#-----------Fin de usuarios 


#----------------Catalogo 
def catalogo_view(request):
    # Carga inicial de todos los productos
    productos = Producto.objects.all()

    # Filtro de búsqueda por nombre de producto
    query = request.GET.get('q')
    if query:
        productos = productos.filter(NombreProducto__icontains=query)

    # Filtro de rango de precio
    min_price = request.GET.get('min_price', 0)
    max_price = request.GET.get('max_price', 1000000)

    # Validación de precios
    try:
        min_price = float(min_price)
    except ValueError:
        min_price = 0  # Valor por defecto si es inválido

    try:
        max_price = float(max_price)
    except ValueError:
        max_price = 1000000  # Valor por defecto si es inválido

    # Aplicación del filtro de precios
    productos = productos.filter(PrecioProducto__gte=min_price, PrecioProducto__lte=max_price)

    # Filtro de categorías
    categorias = request.GET.getlist('categorias')
    if categorias:
        productos = productos.filter(CategoriaProducto__in=categorias)

    # Filtro de tipo de animal
    tipo_animal = request.GET.getlist('tipo_animal')
    if tipo_animal:
        productos = productos.filter(TipoAnimal__in=tipo_animal)

    # Filtro para mostrar solo productos en oferta
    productos_oferta = productos.filter(EstaOferta=True)

    # Mensaje si no hay productos en oferta
    mensaje_oferta = None
    if not productos_oferta.exists():
        mensaje_oferta = "No hay productos en oferta actualmente."

    # Contexto para pasar los productos filtrados al template
    context = {
        'productos': productos,
        'productos_oferta': productos_oferta,
        'mensaje_oferta': mensaje_oferta,
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

    def get_context_data(self, **kwargs):
        context = {}
        context['form'] = kwargs.get('form', self.get_form())
        # Añadimos la lista de SKUs para validación en el frontend
        context['productos_skus'] = self.model.objects.values_list('SKUProducto', flat=True)
        return context

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        sku = request.POST.get('SKUProducto')
        context = self.get_context_data(form=form)

        # busca
        if 'buscar' in request.POST and sku:
            producto = buscar_producto_por_sku(sku)
            if producto:
                # Formatear los precios para mejor visualización
                producto.PrecioProducto = f"${producto.PrecioProducto:,.0f}"
                if producto.EstaOferta:
                    producto.PrecioOferta = f"${producto.PrecioOferta:,.0f}"
                form = self.form_class(instance=producto)
            else:
                form = self.form_class()
            context['form'] = form
            return render(request, self.template_name, context)

        # actualiza o crea
        elif 'crear_actualizar' in request.POST:
            producto = buscar_producto_por_sku(sku)
            
            # Validación de SKU existente solo para creación
            if not producto and self.model.objects.filter(SKUProducto=sku).exists():
                form.add_error('SKUProducto', 'Este SKU ya existe. Por favor, elige otro.')
                context['form'] = form
                return render(request, self.template_name, context)

            if producto:
                form = self.form_class(request.POST, request.FILES, instance=producto)
            else:
                form = self.form_class(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                messages.success(request, 'Producto guardado exitosamente.')
                return redirect(self.success_url)
            
            context['form'] = form
            return render(request, self.template_name, context)

        # borra
        elif 'borrar' in request.POST and sku:
            producto = buscar_producto_por_sku(sku)
            if producto:
                producto.delete()
                messages.success(request, 'Producto eliminado exitosamente.')
                return redirect(self.success_url)
            else:
                messages.error(request, 'No se encontró el producto.')
            return render(request, self.template_name, context)
            
        # limpiar
        elif 'limpiar' in request.POST:
            context['form'] = self.form_class()
            return render(request, self.template_name, context)

        # En caso de error, volvemos a renderizar el formulario
        return render(request, self.template_name, context)
#----------------CRUD de Producto

def checkout_view(request):
    """
    Vista para el proceso de checkout.
    Obtiene el carrito desde las cookies y muestra el resumen del pedido.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger.handlers = []

    try:
        # 1. Obtener el carrito de las cookies
        carrito_str = request.COOKIES.get('carrito', '{}')
        logger.debug(f"Cookie carrito raw: {carrito_str}")

        # 2. Decodificar el JSON
        import json
        carrito_data = json.loads(carrito_str)
        logger.debug(f"Carrito decodificado: {carrito_data}")

        # 3. Procesar el carrito (ahora usando el formato correcto)
        carrito_procesado = {}
        
        for key, item in carrito_data.items():
            # Los datos ya vienen en el formato correcto
            carrito_procesado[key] = {
                'nombre': item['nombre'],
                'precio': float(item['precio']),
                'cantidad': int(item['cantidad']),
                'descripcion': item.get('descripcion', ''),
                'imagen': item.get('imagen', '')
            }
            logger.debug(f"Item procesado - Key: {key}, Datos: {carrito_procesado[key]}")

        # 4. Calcular totales
        subtotal = sum(
            item['precio'] * item['cantidad'] 
            for item in carrito_procesado.values()
        )
        shipping = 0 if subtotal >= 20000 else 3990
        total = subtotal + shipping

        logger.debug(f"Totales calculados - Subtotal: {subtotal}, Shipping: {shipping}, Total: {total}")

        # 5. Preparar contexto
        context = {
            'carrito': carrito_procesado,
            'subtotal': subtotal,
            'shipping': shipping,
            'total': total,
            'debug': True,
            'carrito_raw': carrito_str
        }

        logger.debug(f"Contexto final: {context}")

        # 6. Renderizar template
        return render(request, 'pago/checkout.html', context)

    except json.JSONDecodeError as e:
        logger.error(f"Error decodificando JSON: {str(e)}")
        messages.error(request, 'Error al procesar el carrito')
        return redirect('carrito')
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)
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
        campos_requeridos = ['nombre', 'apellido', 'email', 'telefono', 'direccion']
        for campo in campos_requeridos:
            if not request.POST.get(campo):
                logger.error(f"Campo requerido faltante: {campo}")
                messages.error(request, f'El campo {campo} es requerido')
                return redirect('checkout')
        
        # Obtener datos del formulario
        datos_envio = {
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



#CRUD CLINICA VETERINARIA 
class VeterinariaListView(LoginRequiredMixin, ListView):
    model = Veterinaria
    template_name = 'clinica.html'
    context_object_name = 'veterinarias'
  

def clinica_view(request):
    # Carga inicial de todas las clínicas
    veterinarias = Veterinaria.objects.all()

    # Filtro de búsqueda por nombre de clínica
    query = request.GET.get('q')
    if query:
        veterinarias = veterinarias.filter(NombreVeterinaria__icontains=query)

    # Filtro por localidad
    localidad = request.GET.get('localidad', '')
    if localidad:
        veterinarias = veterinarias.filter(LocalidadVeterinaria__icontains=localidad)

    # Filtro por horarios
    horario_inicio = request.GET.get('horario_inicio')
    if horario_inicio:
        veterinarias = veterinarias.filter(HorarioInicioVeterinaria__gte=horario_inicio)

    horario_fin = request.GET.get('horario_fin')
    if horario_fin:
        veterinarias = veterinarias.filter(HorarioCierreVeterinaria__lte=horario_fin)

    

    # Verificar si es una solicitud AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Obtener solo los campos necesarios y convertir a una lista de diccionarios
        data = list(veterinarias.values(
            'NombreVeterinaria',
            'LocalidadVeterinaria',
            'HorarioInicioVeterinaria',
            'HorarioCierreVeterinaria',
        ))
        return JsonResponse({'veterinarias': data})  # Responder con los datos en formato JSON

    # Contexto normal para renderizado en la página (no es una solicitud AJAX)
    context = {
        'veterinarias': veterinarias,
        'localidad': localidad,  # Asegúrate de que 'localidad' esté disponible en el template
        'horario_inicio': request.GET.get('horario_inicio', ''),
        'horario_fin': request.GET.get('horario_fin', '')
    }

    return render(request, 'clinica.html', context)


class VeterinariaCreateView(LoginRequiredMixin, CreateView):
    
    
    model = Veterinaria
    form_class = VeterinariaForm
    template_name = 'clinica.html'

    def form_valid(self, form):
        # Verificar si ya existe una veterinaria con el mismo nombre
        nombre_veterinaria = form.cleaned_data.get('NombreVeterinaria')
        correo_veterinaria = form.cleaned_data.get('CorreoVeterinaria')  # Suponiendo que el campo de correo está en el formulario
        
        # Validar que no exista una veterinaria con el mismo nombre o correo
        if Veterinaria.objects.filter(NombreVeterinaria=nombre_veterinaria).exists():
            return JsonResponse({
                'success': False,
                'errors': {'NombreVeterinaria': 'Ya existe una veterinaria con ese nombre.'}
            })
        
        if Veterinaria.objects.filter(email=correo_veterinaria).exists():
            return JsonResponse({
                'success': False,
                'errors': {'CorreoVeterinaria': 'Ya existe una veterinaria con ese correo.'}
            })
        
        # Si no hay duplicados, guardar la veterinaria
        veterinaria = form.save()
        return JsonResponse({
            'success': True,'reload': True,
            'veterinaria': {
                'id': veterinaria.CodigoVeterinaria,
                'NombreVeterinaria': veterinaria.NombreVeterinaria,
                'LocalidadVeterinaria': veterinaria.LocalidadVeterinaria,
            }
        })

    def form_invalid(self, form):
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })
class VeterinariaUpdateView(LoginRequiredMixin, UpdateView):
    model = Veterinaria
    form_class = VeterinariaForm
    template_name = 'clinica.html'
    success_url = reverse_lazy('veterinaria')

    def validar_duplicados(self, form):
        errores = {}
        nombre_veterinaria = form.cleaned_data.get('NombreVeterinaria')
        correo_veterinaria = form.cleaned_data.get('CorreoVeterinaria')

        if Veterinaria.objects.filter(NombreVeterinaria=nombre_veterinaria).exclude(pk=self.object.pk).exists():
            errores['NombreVeterinaria'] = 'Ya existe una veterinaria con ese nombre.'

        if Veterinaria.objects.filter(email=correo_veterinaria).exclude(pk=self.object.pk).exists():
            errores['CorreoVeterinaria'] = 'Ya existe una veterinaria con ese correo.'

        return errores

    def form_valid(self, form):
        errores = self.validar_duplicados(form)
        if errores:
            return JsonResponse({'success': False, 'errors': errores})
        # Guardar y responder con éxito y señal de recarga
        response = super().form_valid(form)
        return JsonResponse({'success': True, 'reload': True})

    def form_invalid(self, form):
        return JsonResponse({'success': False, 'errors': form.errors})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('error'):
            context['error_message'] = 'Hubo un problema al guardar los cambios. Por favor, intente de nuevo.'
        return context

class VeterinariaDeleteView(DeleteView):
    model = Veterinaria
    template_name = 'veterinaria_confirm_delete.html'
    success_url = reverse_lazy('veterinaria_list')

    def form_valid(self, form):
        # Lógica personalizada para eliminación
        veterinaria = self.get_object()

        try:
           

            # Eliminar la veterinaria
            veterinaria.delete()

            # Retornar éxito para recargar la página
            return JsonResponse({'success': True, 'reload': True})

        except Exception as e:
            return JsonResponse({'error': f'Error al eliminar: {str(e)}'}, status=500)

    def form_invalid(self, form):
        return JsonResponse({'error': 'Error al eliminar la veterinaria'}, status=400)

    
#CRUD VETERINARIO
class VeterinarioListView(LoginRequiredMixin, ListView):
    model = Veterinario
    template_name = 'veterinario.html'
    context_object_name = 'veterinarios'


def get_veterinarias(request):
    search = request.GET.get('search', '')
    veterinarias = Veterinaria.objects.filter(
        nombre__icontains=search
    ).values('CodigoVeterinaria', 'nombre')[:10]  # Limitamos a 10 resultados
    return JsonResponse(list(veterinarias), safe=False)

def veterinario_view(request):
    # Carga inicial de todos los veterinarios
    veterinarios = Veterinario.objects.all()

    # Filtro por localidad
    localidad = request.GET.get('localidad')
    if localidad:
        veterinarios = veterinarios.filter(veterinaria__LocalidadVeterinaria__icontains=localidad)

    # Filtro de búsqueda por nombre de la clínica (especialidad en este caso)
    query = request.GET.get('q')
    if query:
        veterinarios = veterinarios.filter(especialidad__icontains=query)

    # Filtro por horarios
    horario_inicio = request.GET.get('horario_inicio')
    if horario_inicio:
        veterinarios = veterinarios.filter(horario_inicio__gte=horario_inicio)

    horario_fin = request.GET.get('horario_fin')
    if horario_fin:
        veterinarios = veterinarios.filter(horario_fin__lte=horario_fin)

    # Verificar si es una solicitud AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        veterinarias_data = veterinarios.values(
            'veterinaria__NombreVeterinaria',
            'veterinaria__LocalidadVeterinaria',
            'veterinaria__HorarioInicioVeterinaria',
            'veterinaria__HorarioCierreVeterinaria',
        )
        return JsonResponse({'veterinarias': list(veterinarias_data)})

    # Contexto normal para renderizado en la página
    context = {
        'veterinarios': veterinarios,
        'localidad': request.GET.get('localidad', ''),
        'query': request.GET.get('q', ''),
        'horario_inicio': request.GET.get('horario_inicio', ''),
        'horario_fin': request.GET.get('horario_fin', ''),
    }

    return render(request, 'veterinario.html', context)


class VeterinarioCreateView(LoginRequiredMixin, CreateView):
    model = Veterinario
    form_class = VeterinarioForm
    template_name = 'veterinario.html'  # Cambiar la plantilla según corresponda

    def form_valid(self, form):
        # Obtener el código del veterinario desde el formulario
        codigo_veterinario = form.cleaned_data.get('codigo_veterinario')
        usuario = form.cleaned_data.get('usuario')
        veterinaria = form.cleaned_data.get('veterinaria')

        # Verificar si ya existe un veterinario con el mismo código
        if Veterinario.objects.filter(codigo_veterinario=codigo_veterinario).exists():
            return JsonResponse({
                'success': False,
                'errors': {'codigo_veterinario': 'Este código de veterinario ya está registrado.'}
            })

        # Validar si el usuario ya está registrado como veterinario
        if Veterinario.objects.filter(usuario=usuario).exists():
            return JsonResponse({
                'success': False,
                'errors': {'usuario': 'Este usuario ya está registrado como veterinario.'}
            })

        # Validación de la veterinaria (opcional)
        if veterinaria and Veterinaria.objects.filter(CodigoVeterinaria=veterinaria.CodigoVeterinaria).exists():
            pass  # Validaciones adicionales si es necesario
        
        # Guardar el nuevo veterinario si las validaciones son correctas
        veterinario = form.save()

        # Si el formulario es válido, enviar una respuesta en JSON con la información del veterinario
        return JsonResponse({
            'success': True,
            'reload': True,
            'veterinario': {
                'codigo_veterinario': veterinario.codigo_veterinario,  # Nuevo campo
                'nombre': str(veterinario.usuario.NombreUsuario),  # Nombre del veterinario
                'especialidad': veterinario.especialidad,
                'veterinaria': veterinario.veterinaria.NombreVeterinaria if veterinario.veterinaria else 'No asociada',
            }
        })

    def form_invalid(self, form):
        # Si el formulario no es válido, retornar los errores del formulario en JSON
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })

        
class VeterinarioUpdateView(LoginRequiredMixin, UpdateView):
    model = Veterinario
    form_class = VeterinarioForm
    template_name = 'veterinario.html'
    success_url = reverse_lazy('veterinario_list')  # Cambiar según la URL de éxito deseada

    def validar_duplicados(self, form):
        errores = {}
        codigo_veterinario = form.cleaned_data.get('codigo_veterinario')

        # Validación de duplicado por código veterinario
        if Veterinario.objects.filter(codigo_veterinario=codigo_veterinario).exclude(pk=self.object.pk).exists():
            errores['codigo_veterinario'] = 'Ya existe un veterinario con este código.'

        return errores

    def form_valid(self, form):
        # Verificar duplicados antes de guardar el formulario
        errores = self.validar_duplicados(form)
        if errores:
            return JsonResponse({'success': False, 'errors': errores})

        # Guardar el formulario y enviar respuesta
        response = super().form_valid(form)
        return JsonResponse({'success': True, 'reload': True})

    def form_invalid(self, form):
        # Manejo de formulario inválido, devolver los errores en formato JSON
        return JsonResponse({'success': False, 'errors': form.errors})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Mostrar un mensaje de error si existe un parámetro 'error' en la URL
        if self.request.GET.get('error'):
            context['error_message'] = 'Hubo un problema al guardar los cambios. Por favor, intente de nuevo.'
        return context



class VeterinarioDeleteView(LoginRequiredMixin, DeleteView):
    model = Veterinario
    template_name = 'veterinario_confirm_delete.html'
    success_url = reverse_lazy('veterinario_list')

    def form_valid(self, form):
        try:
            # Eliminar el veterinario
            veterinario = self.get_object()
            veterinario.delete()

            # Retornar éxito en formato JSON
            return JsonResponse({'success': True, 'reload': True})

        except Exception as e:
            # Si ocurre un error, devolver mensaje de error
            return JsonResponse({'error': f'Error al eliminar: {str(e)}'}, status=500)

    def form_invalid(self, form):
        # Si ocurre un error en la eliminación, devolver mensaje de error
        return JsonResponse({'error': 'Error al eliminar el veterinario'}, status=400)
    

#CRUD CITAS
class CitaVeterinariaListView(LoginRequiredMixin, ListView):
    model = CitaVeterinaria
    template_name = 'cita.html'
    context_object_name = 'citas'
  


    def get_queryset(self):
        queryset = super().get_queryset().filter(usuario=self.request.user)
        estado = self.request.GET.get('estado')
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        veterinaria = self.request.GET.get('veterinaria')

        if estado:
            queryset = queryset.filter(estado=estado)
        if fecha_desde:
            queryset = queryset.filter(fecha__gte=fecha_desde)
        if fecha_hasta:
            queryset = queryset.filter(fecha__lte=fecha_hasta)
        if veterinaria:
            queryset = queryset.filter(veterinaria_id=veterinaria)

        return queryset.order_by('-fecha', '-hora')
    
    
    
    
def cita_view(request):
    #carga incial de todas las veterinarios
    veterinarios = CitaVeterinaria.objects.all()
    
    # Filtro de búsqueda por especialidad de veterinario
    query = request.GET.get('q')
    if query:
        veterinarios = CitaVeterinaria.filter( especialidad__icontains=query)
    context={
        'veterinarios':veterinarios
    }
    return render(request, 'veterinario.html', context)




class CitaVeterinariaCreateView(LoginRequiredMixin, CreateView):
    model = CitaVeterinaria
    form_class = CitaVeterinariaForm
    template_name = 'cita.html'
    success_url = reverse_lazy('cita_list')

class CitaVeterinariaUpdateView(LoginRequiredMixin , UpdateView):
    model = CitaVeterinaria
    form_class = CitaVeterinariaForm
    template_name = 'cita.html'
    success_url = reverse_lazy('cita_list')

class CitaVeterinariaDeleteView(LoginRequiredMixin, DeleteView):
    model = CitaVeterinaria
    template_name = 'cita_confirm_delete.html'
    success_url = reverse_lazy('cita_list')
    
    
    
class ServicioListView(LoginRequiredMixin, ListView):
    model = Servicio
    template_name = 'servicios.html'
    context_object_name = 'servicios'
  
    
    
def servicio_view(request):
    #carga incial de todas las servicios
    servicios = Servicio.objects.all()
    
    # Filtro de búsqueda por especialidad de servicios
    query = request.GET.get('q')
    if query:
        servicios = Servicio.filter( TipoServicio__icontains=query)
    context={
        'servicios':servicios
    }
    return render(request, 'servicios.html', context)


class ServicioCreateView(LoginRequiredMixin, CreateView):
    model = Servicio
    form_class = ServicioForm
    template_name = 'servicios.html'
    success_url = reverse_lazy('servicio_list')

class ServicioUpdateView(LoginRequiredMixin, UpdateView):
    model = Servicio
    form_class = ServicioForm
    template_name = 'servicios.html'
    success_url = reverse_lazy('servicio_list')

class ServicioDeleteView(LoginRequiredMixin, DeleteView):
    model = Servicio
    template_name = 'servicio_confirm_delete.html'
    success_url = reverse_lazy('servicio_list')
    
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
    
    
    
    
    

