from django.core.exceptions import PermissionDenied,ValidationError
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, FormView
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.urls import include, path, reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from .models import Producto, CustomUser
from .forms import ProductoForm, RegistroUsuarioForm
from django.contrib.auth.decorators import login_required
from django.db.models import Q
# from django.utils import timezone,send_confirmation_email, send_cancellation_email
from .models import CitaVeterinaria,Servicio,Veterinario,Veterinaria
from .forms import CitaVeterinariaForm
from django.core.serializers import serialize
import json
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta,date

from django.utils import timezone





# Aqui van las famosas vistas, no confundir

class RegistroUsuarioView(FormView):
    template_name = 'usuario/late_registration.html'
    form_class = RegistroUsuarioForm
    success_url = reverse_lazy('home')  # Asegúrate que esta URL exista y esté correcta

    def form_valid(self, form):
        if form.is_valid():
            print("Formulario válido")
            form.save()
            messages.success(self.request, '¡Tu cuenta ha sido creada exitosamente!')
        else:
            print("Formulario no es válido")
            messages.error(self.request, 'Por favor, revisa los datos.')
        return super().form_valid(form)

def login_view(request):
    return render(request, 'login.html')

def home_view(request):
    return render(request, 'home.html')

def vetdate_view(request):
    return render(request, 'cita.html')

def storefront_view(request):
    return render(request, 'catalogo.html')

def pago_view(request):
    return render(request,'checkout.html')

def carrito_view(request):
    cart_items = [
        {
            'id': 1,
            'name': 'Dog Collar',
            'description': 'Adjustable nylon dog collar',
            'image': 'https://via.placeholder.com/150',
            'price': 12.99,
            'quantity': 2
        },
        {
            'id': 2,
            'name': 'Cat Toys',
            'description': 'Set of 3 interactive cat toys',
            'image': 'https://via.placeholder.com/150',
            'price': 9.99,
            'quantity': 1
        },
        {
            'id': 3,
            'name': 'Pet Shampoo',
            'description': 'Natural pet shampoo, 16 oz',
            'image': 'https://via.placeholder.com/150',
            'price': 7.50,
            'quantity': 1
        },
        {
            'id': 4,
            'name': 'Dog Bed',
            'description': 'Orthopedic memory foam dog bed',
            'image': 'https://via.placeholder.com/150',
            'price': 39.99,
            'quantity': 1
        }
    ]

    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    shipping = 5.00
    tax = subtotal * 0.1
    total = subtotal + shipping + tax

    context = {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total
    }

    return render(request, 'carrito.html', context)

#Catalogo 

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




#CRUD de Producto
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
    
    
   
@login_required
def lista_citas(request):
    # Filtros desde URL
    estado = request.GET.get('estado')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    veterinaria = request.GET.get('veterinaria')

    # Query base
    citas = CitaVeterinaria.objects.select_related(
        'veterinaria', 'veterinario'
    ).filter(usuario=request.user)

    # Aplicar filtros
    if estado:
        citas = citas.filter(estado=estado)
    if fecha_desde:
        citas = citas.filter(fecha__gte=fecha_desde)
    if fecha_hasta:
        citas = citas.filter(fecha__lte=fecha_hasta)
    if veterinaria:
        citas = citas.filter(veterinaria_id=veterinaria)

    # Ordenar
    citas = citas.order_by('-fecha', '-hora')

    # Paginación
    paginator = Paginator(citas, 10)
    page = request.GET.get('page')
    citas_paginadas = paginator.get_page(page)

    # Datos para filtros
    veterinarias = Veterinaria.objects.filter(DisponibilidadVeterinaria='S')

    context = {
        'citas': citas_paginadas,
        'veterinarias': veterinarias,
        'estados': CitaVeterinaria.ESTADO_CHOICES,
        'filtros': {
            'estado': estado,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
            'veterinaria': veterinaria
        }
    }
    return render(request, 'veterinaria/citas.html', context)

@login_required
@require_http_methods(["POST"])
def crear_cita(request):
    form = CitaVeterinariaForm(request.POST)
    
    # if form.is_valid():
    #     try:
    #         cita = form.save(commit=False)
    #         cita.usuario = request.user
    #         cita.save()

    #         # # Enviar correo de confirmación
    #         # try:
    #         #     send_confirmation_email(cita)
    #         # except Exception as e:
    #         #     # Loguear el error pero no afectar la creación de la cita
    #         #     print(f"Error enviando correo: {str(e)}")

    #         # return JsonResponse({
    #         #     'success': True,
    #         #     'message': 'Cita creada exitosamente',
    #         #     'cita_id': cita.id
    #         # })
    #     except ValidationError as e:
    #         return JsonResponse({
    #             'success': False,
    #             'errors': {'__all__': [str(e)]}
    #         })
    
    # return JsonResponse({
    #     'success': False,
    #     'errors': form.errors
    # })

@login_required
@require_http_methods(["GET", "POST"])
def editar_cita(request, pk):
    cita = get_object_or_404(CitaVeterinaria, pk=pk, usuario=request.user)
    
    if cita.estado not in ['PENDIENTE', 'CONFIRMADA']:
        return JsonResponse({
            'success': False,
            'error': 'No se puede editar una cita que ya está cancelada'
        })

    if request.method == "GET":
        return JsonResponse({
            'id': cita.id,
            'servicio': cita.servicio,
            'veterinaria': cita.veterinaria.id,
            'veterinario': cita.veterinario.id,
            'fecha': cita.fecha.isoformat(),
            'hora': cita.hora.strftime('%H:%M'),
            'notas': cita.notas or ''
        })

    form = CitaVeterinariaForm(request.POST, instance=cita)
    if form.is_valid():
        cita = form.save()
        return JsonResponse({
            'success': True,
            'message': 'Cita actualizada exitosamente'
        })
    
    return JsonResponse({
        'success': False,
        'errors': form.errors
    })

@login_required
@require_http_methods(["POST"])
def cancelar_cita(request, pk):
    cita = get_object_or_404(CitaVeterinaria, pk=pk, usuario=request.user)
    
    if cita.estado not in ['PENDIENTE', 'CONFIRMADA']:
        return JsonResponse({
            'success': False,
            'error': 'Esta cita ya no puede ser cancelada'
        })

    # try:
    #     cita.estado = 'CANCELADA'
    #     cita.save()

    #     # Enviar correo de cancelación
    #     try:
    #         send_cancellation_email(cita) 
    #     except Exception as e:
    #         print(f"Error enviando correo de cancelación: {str(e)}")

    #     return JsonResponse({
    #         'success': True,
    #         'message': 'Cita cancelada exitosamente'
    #     })
    # except Exception as e:
    #     return JsonResponse({
    #         'success': False,
    #         'error': str(e)
    #     })

@login_required
def obtener_veterinarios(request):
    veterinaria_id = request.GET.get('veterinaria_id')
    if not veterinaria_id:
        return JsonResponse({'veterinarios': []})

    veterinarios = Veterinario.objects.filter(
        veterinaria_id=veterinaria_id,
        usuario__is_active=True
    ).values('id', 'usuario__NombreUsuario', 'especialidad')

    return JsonResponse({'veterinarios': list(veterinarios)})




@login_required
def api_citas_calendario(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    # Convertir fechas de string a datetime
    start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
    end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
    
    # Obtener citas dentro del rango
    citas = CitaVeterinaria.objects.filter(
        usuario=request.user,
        fecha__range=[start_date.date(), end_date.date()]
    ).select_related('veterinaria', 'veterinario')
    
    # Mapeo de colores según estado
    color_map = {
        'PENDIENTE': '#ffc107',  # Amarillo
        'CONFIRMADA': '#28a745',  # Verde
        'CANCELADA': '#dc3545',   # Rojo
    }
    
    # Formatear citas para FullCalendar
    events = []
    for cita in citas:
        start_time = datetime.combine(cita.fecha, cita.hora)
        end_time = start_time + timedelta(minutes=30)  # Duración estimada
        
        events.append({
            'id': cita.id,
            'title': f"{cita.servicio} - {cita.veterinario}",
            'start': start_time.isoformat(),
            'end': end_time.isoformat(),
            'color': color_map.get(cita.estado, '#ffc107'),
            'extendedProps': {
                'estado': cita.estado,
                'veterinaria': cita.veterinaria.NombreVeterinaria,
                'veterinario': str(cita.veterinario),
                'notas': cita.notas or ''
            }
        })
    
    return JsonResponse(events, safe=False)

@login_required
def api_horarios_disponibles(request):
    fecha = request.GET.get('fecha')
    veterinario_id = request.GET.get('veterinario_id')
    
    if not all([fecha, veterinario_id]):
        return JsonResponse({
            'success': False,
            'error': 'Parámetros incompletos'
        })
    
    try:
        veterinario = Veterinario.objects.get(id=veterinario_id)
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        
        # Obtener horario de la veterinaria
        inicio = veterinario.veterinaria.HorarioInicioVeterinaria
        fin = veterinario.veterinaria.HorarioCierreVeterinaria
        
        # Obtener citas existentes
        citas_existentes = CitaVeterinaria.objects.filter(
            veterinario=veterinario,
            fecha=fecha_obj,
            estado__in=['PENDIENTE', 'CONFIRMADA']
        ).values_list('hora', flat=True)
        
        # Generar horarios disponibles (intervalos de 30 minutos)
        horarios_disponibles = []
        hora_actual = inicio
        while hora_actual <= fin:
            if hora_actual not in citas_existentes:
                horarios_disponibles.append(hora_actual.strftime('%H:%M'))
            hora_actual = (datetime.combine(date.today(), hora_actual) + 
                         timedelta(minutes=30)).time()
        
        return JsonResponse({
            'success': True,
            'horarios': horarios_disponibles
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })