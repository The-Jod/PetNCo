from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, FormView
from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.urls import include, path, reverse_lazy
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from .models import Producto, CustomUser
from .forms import ProductoForm, RegistroUsuarioForm



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

    # Filtro de categorías (Ya la implemente)
    categorias = request.GET.getlist('categorias')
    if categorias:
        productos = productos.filter(DescripcionProducto__icontains=categorias[0])

    # Filtro de tipo de animal
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
        'precio': producto.PrecioProducto,
        'precio_oferta': producto.PrecioOferta if producto.EstaOferta else None,
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

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        sku = request.POST.get('SKUProducto')

        # busca
        if 'buscar' in request.POST and sku:
            producto = buscar_producto_por_sku(sku)
            if producto:
                form = ProductoForm(instance=producto)
            else:
                form = ProductoForm()
            return render(request, self.template_name, {'form': form})

        # actualiza
        elif 'crear_actualizar' in request.POST:
            producto = buscar_producto_por_sku(sku)

            if producto:
                form = ProductoForm(request.POST, request.FILES, instance=producto)
            else:
                form = ProductoForm(request.POST, request.FILES)

            if form.is_valid():
                form.save()
                return redirect(self.success_url)

            return render(request, self.template_name, {'form': form})

        # borra
        elif 'borrar' in request.POST and sku:
            producto = buscar_producto_por_sku(sku)
            
            if producto:
                producto.delete()
                return redirect(self.success_url)
            
            else:
                return render(request, self.template_name, {'form': form})
            
        # limpiar
        elif 'limpiar' in request.POST and sku:
            producto = buscar_producto_por_sku(sku)
    
            if producto:
                return render(request, self.template_name, {'form': form})
            else:
                return render(request, self.template_name, {'form': form})

        # En caso de error, volvemos a renderizar el formulario
        return render(request, self.template_name, {'form': form})