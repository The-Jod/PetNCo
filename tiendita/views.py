from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, FormView
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import include, path, reverse_lazy, reverse
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from .models import Producto, CustomUser, Orden, OrdenItem
from .forms import ProductoForm, RegistroUsuarioForm, CustomLoginForm
from decimal import Decimal
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions
from transbank.error.transbank_error import TransbankError
from django.conf import settings
import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
import json
from django.views.decorators.http import require_POST
import random
import logging
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

# Aqui van las famosas vistas, no confundir
def home_view(request):
    return render(request, 'home.html')

def vetdate_view(request):
    return render(request, 'cita.html')

def storefront_view(request):
    return render(request, 'pago/catalogo.html')

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

