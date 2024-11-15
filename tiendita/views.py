from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, FormView
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LoginView
from django.contrib import messages
from django.urls import include, path, reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from .models import Producto, CustomUser
from .forms import ProductoForm, RegistroUsuarioForm, CustomLoginForm
from decimal import Decimal

# Aqui van las famosas vistas, no confundir
def home_view(request):
    return render(request, 'home.html')

def vetdate_view(request):
    return render(request, 'cita.html')

def storefront_view(request):
    return render(request, 'catalogo.html')

def pago_view(request):
    return render(request,'checkout.html')

#------------Carrito 
def agregar_al_carrito(request, sku):
    producto = get_object_or_404(Producto, SKUProducto=sku)
    carrito = request.session.get('carrito', {})
    
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

    request.session['carrito'] = carrito
    request.session.modified = True
    return redirect('carrito')

# Ver el carrito
def carrito_view(request):
    carrito = request.session.get('carrito', {})
    
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

    return render(request, 'carrito.html', context)

def actualizar_cantidad(request):
    if request.method == 'POST':
        sku = request.POST.get('item_id')
        cantidad = int(request.POST.get('quantity'))
        
        carrito = request.session.get('carrito', {})
        if sku in carrito:
            # Verificar stock disponible
            producto = Producto.objects.get(SKUProducto=sku)
            cantidad = min(cantidad, producto.StockProducto)  # Limitar a stock disponible
            
            carrito[sku]['cantidad'] = cantidad
            request.session['carrito'] = carrito
            request.session.modified = True
            
            # Recalcular totales
            subtotal = sum(float(item['precio']) * item['cantidad'] for item in carrito.values())
            shipping = 0 if subtotal >= 20000 else 3990
            total = subtotal + shipping
            
            return JsonResponse({
                'status': 'ok',
                'subtotal': subtotal,
                'shipping': shipping,
                'total': total,
                'quantity': cantidad  # Devolver la cantidad ajustada
            })
    
    return JsonResponse({'status': 'error'}, status=400)

# Eliminar un producto del carrito
def eliminar_del_carrito(request, sku):
    carrito = request.session.get('carrito', {})

    if str(sku) in carrito:
        del carrito[str(sku)]
        request.session['carrito'] = carrito

    return redirect('carrito')

# Limpiar el carrito
def limpiar_carrito(request):
    if request.method == 'POST':
        # Limpiar el carrito en la sesión
        request.session['carrito'] = {}
        request.session.modified = True
        messages.success(request, 'El carrito ha sido vaciado exitosamente')
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
    carrito = request.session.get('carrito', {})
    
    if not carrito:
        messages.warning(request, 'No puedes proceder al pago con un carrito vacío')
        return redirect('carrito')
        
    # ... resto del código del checkout ...

