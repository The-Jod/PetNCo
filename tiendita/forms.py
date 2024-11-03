from django import forms
from .models import Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = [
            'SKUProducto', 
            'NombreProducto', 
            'StockProducto', 
            'PrecioProducto', 
            'DescripcionProducto', 
            'EstaOferta', 
            'PrecioOferta', 
            'CategoriaProducto', 
            'TipoAnimal', 
            'ImagenProducto'
        ]

        widgets = {
            'SKUProducto': forms.TextInput(attrs={'class': 'form-control', 
                                                    'placeholder': 'SKU'}),

            'NombreProducto': forms.TextInput(attrs={'class': 'form-control', 
                                                    'placeholder': 'Nombre'}),

            'StockProducto': forms.NumberInput(attrs={'class': 'form-control', 
                                                    'placeholder': 'Stock'}),

            'PrecioProducto': forms.NumberInput(attrs={'class': 'form-control',
                                                    'placeholder': 'Precio del producto'}),

            'DescripcionProducto': forms.Textarea(attrs={'class': 'form-control', 
                                                    'placeholder': 'Descripción'}),

            'EstaOferta': forms.CheckboxInput(attrs={'class': 'form-check-input'}),

            'PrecioOferta': forms.NumberInput(attrs={'class': 'form-control', 
                                                     'placeholder': 'Precio con descuento'}),

            'CategoriaProducto': forms.Select(attrs={'class': 'form-select'}),

            'TipoAnimal': forms.Select(attrs={'class': 'form-select'}), 
            
            'ImagenProducto': forms.FileInput(attrs={'class': 'form-control'}),
        }