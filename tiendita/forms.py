from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Producto, UsuarioProfile


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
            
            'ImagenProducto': forms.ClearableFileInput(attrs={'class': 'form-control',}),

        }

        def __init__(self, *args, **kwargs):
            super(ProductoForm, self).__init__(*args, **kwargs)

        # Busca la imagen de producto, Fue un parto lograr que funcionara, xfavor no le muevan.
            if self.instance and self.instance.pk:
                self.fields['ImagenProducto'].widget = forms.FileInput(attrs={
                    'class': 'form-control',
                })
            else:
                self.fields['ImagenProducto'].widget = forms.ClearableFileInput(attrs={
                'class': 'form-control',
            })
        
class UsuarioRegistroForm(UserCreationForm):
    # Añadimos el campo de RutUsuario al formulario
    RutUsuario = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'RUT'})
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']  # Solo los campos necesarios de User

    def save(self, commit=True):
        # Guardamos el usuario del modelo User
        user = super().save(commit=False)
        if commit:
            user.save()
        
        # Creamos y guardamos el perfil del usuario (UsuarioProfile)
        usuario_profile = UsuarioProfile(
            user=user,
            RutUsuario=self.cleaned_data['RutUsuario']
        )
        if commit:
            usuario_profile.save()

        return user