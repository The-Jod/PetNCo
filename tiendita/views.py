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




class Product_ListView(ListView):
    model = Producto
    template_name = 'catalog/product_list.html'
    context_object_name = 'productos'


class Product_CreateView(CreateView):
    model = Producto
    fields = ['SKUProducto', 'NombreProducto', 'StockProducto', 'PrecioProducto', 'DescripcionProducto', 'TipoAnimal']
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog')

    
class Product_UpdateView(UpdateView):
    model = Producto
    fields = ['NombreProducto', 'StockProducto', 'PrecioProducto', 'DescripcionProducto', 'TipoAnimal']
    template_name = 'catalog/product_form.html'
    success_url = reverse_lazy('catalog')

class Product_DeleteView(DeleteView):
    model = Producto
    template_name = 'catalog/product_confirm_delete.html'
    success_url = reverse_lazy('catalog')