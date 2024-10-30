from django.shortcuts import render
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth import views as auth_views
from django.urls import include, path, reverse_lazy
from .models import Producto
from django.core.paginator import Paginator

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

def pago_view(request):
    return render(request,'checkout.html')

def carrito_view(request):
    return render(request,'carrito.html')

# No se imaginan el dolor que fue cranearme esta wea, a la proxima la GPTEO
def catalogo_view(request):
    # Obtiene todos los productos
    productos = Producto.objects.all()

    # Filtro de búsqueda por nombre de producto
    query = request.GET.get('q')
    if query:
        productos = productos.filter(NombreProducto__icontains=query)

     # Filtro de rango de precio
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    # Verificar si min_price y max_price son válidos
    if min_price:
        try:
            min_price = float(min_price)
        except ValueError:
            min_price = 0  # Constante en caso de error
    else:
        min_price = 0

    if max_price:
        try:
            max_price = float(max_price)
        except ValueError:
            max_price = 1000000  # Constante en caso de error
    else:
        max_price = 1000000

    productos = productos.filter(PrecioProducto__gte=min_price, PrecioProducto__lte=max_price)

    # Filtro de categorías (Hay que implementar esta wea pero polla idea como)
    categorias = request.GET.getlist('categorias')
    if categorias:
        productos = productos.filter(DescripcionProducto__icontains=categorias[0])

    # Filtro de tipo de animal (float)
    tipo_animal = request.GET.getlist('tipo_animal')
    if tipo_animal:
        productos = productos.filter(TipoAnimal__in=tipo_animal)

    context = {
        'productos': productos,
    }

    return render(request, 'catalogo/product_list.html', context)


class Product_ListView(ListView):
    model = Producto
    template_name = 'catalogo/product_list.html'
    context_object_name = 'productos'


class Product_CreateView(CreateView):
    model = Producto
    fields = ['SKUProducto', 'NombreProducto', 'StockProducto', 'PrecioProducto', 'DescripcionProducto', 'TipoAnimal']
    template_name = 'catalogo/product_form.html'
    success_url = reverse_lazy('catalog')

    
class Product_UpdateView(UpdateView):
    model = Producto
    fields = ['NombreProducto', 'StockProducto', 'PrecioProducto', 'DescripcionProducto', 'TipoAnimal']
    template_name = 'catalogo/product_form.html'
    success_url = reverse_lazy('catalog')

class Product_DeleteView(DeleteView):
    model = Producto
    template_name = 'catalogo/product_confirm_delete.html'
    success_url = reverse_lazy('catalog')