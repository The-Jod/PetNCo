from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import Producto, CustomUser


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


class RegistroUsuarioForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['RutUsuario', 'EmailUsuario', 'password1', 'password2']  # Incluye solo los campos que necesitas
        widgets = {
            'RutUsuario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Si termina en K, Reemplazalo por 11'}),
            'EmailUsuario': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Correo Electrónico'}),
        }
        labels = {
            'RutUsuario' : ('RUT. Sin punto ni guion'),
            'EmailUsuario' : ('Correo Electronico'),  
        }
        error_messages = {
            'RutUsuario': {
                'invalid': "El RUT es invalido.",
                'unique' : "El RUT ya está registrado.",
                'required': "Por favor, ingresa tu RUT."
            },
            'EmailUsuario': {
                'invalid': "Por favor, ingresa un correo electrónico válido.",
                'required': "El correo electrónico es obligatorio."
            },
            'password2': {
                'password_mismatch': "Las contraseñas no coinciden.",
            },
        }
    

class CustomLoginForm(AuthenticationForm):
    username = forms.IntegerField(
        label="RUT Usuario",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'RUT'}),
        error_messages = {
            'RutUsuario': {
                'invalid': "El RUT es invalido.",
                'required': "Por favor, ingresa tu RUT."
            }
        }
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        error_messages = {
            'Contraseña': {
                'invalid': "El Rut o la Contraseña no coinciden.",
                'required': "Ingresa la contraseña."
            }
        }
    )

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError("Esta cuenta está inactiva.", code='inactive')

    def clean(self):
        cleaned_data = super().clean()
        rut = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if rut and password:
            user = authenticate(username=rut, password=password)
            if user is None:
                raise forms.ValidationError("Las credenciales no son válidas.")
        
        return cleaned_data