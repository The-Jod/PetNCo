# Standard library imports

from datetime import datetime, timedelta, date

# Django imports
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
import os

# Local application imports
from .models import Producto, CustomUser , CitaVeterinaria, Servicio, Veterinario, Veterinaria
class ProductoForm(forms.ModelForm):
    # Validador para SKU numérico
    SKUProducto = forms.CharField(
        validators=[
            RegexValidator(
                regex='^[0-9]+$',
                message='El SKU debe contener solo números',
                code='invalid_sku'
            )
        ],
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese SKU numérico'
        })
    )

    NombreProducto = forms.CharField(
        validators=[
            RegexValidator(
                regex='^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                message='El nombre del producto debe contener solo letras y espacios',
                code='invalid_nombre'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese el Nombre de su producto',
            
        })
    )
    
    StockProducto = forms.CharField(
         validators=[
            RegexValidator(
                regex='^[0-9]+$',
                message='El stock debe ser un número entero',
                code='invalid_stock'
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Stock Disponible',
            
        })
    )
    
    # Precio normal también como string con formato de moneda
    PrecioProducto = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '$0',
            'data-type': 'currency'
        })
    )
    
    
    DescripcionProducto = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ejemplo : Peso en Kg y  Sabor',
           
        })
    )
    
    
    EstaOferta = forms.CharField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    # Campo de precio oferta como string con formato de moneda
    PrecioOferta = forms.CharField(
        required=False,  # Opcional ya que es precio de oferta
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '$0',
            'data-type': 'currency'
        })
    )


    
# Campo para CategoriaProducto (con opciones limitadas)
    CATEGORIAS = [
        (0.1, 'Alimentos'),
        (0.2, 'Accesorios'),
        (0.3, 'Juguetes'),
        (0.4, 'Camas y rascadores')
    ]
    
    CategoriaProducto = forms.ChoiceField(
        choices=CATEGORIAS,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )

    # Campo para TipoAnimal (con opciones limitadas)
    TIPO_ANIMAL = [
        (0.1, 'Gato'),
        (0.2, 'Perro'),
        (0.3, 'Ave'),
        (0.4, 'Hamster')
    ]
    
    TipoAnimal = forms.ChoiceField(
        choices=TIPO_ANIMAL,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    
    ImagenProducto = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
        })
    )
    

    class Meta:
        model = Producto
        fields = ['SKUProducto', 'NombreProducto', 'DescripcionProducto', 
                 'PrecioProducto', 'PrecioOferta', 'ImagenProducto', 
                 'EstaOferta', 'CategoriaProducto', 'TipoAnimal', 'StockProducto']
        
    def clean_SKUProducto(self):
        sku = self.cleaned_data.get('SKUProducto')
        if not sku.isdigit():
            raise forms.ValidationError('El SKU debe contener solo números')
        return sku

    def clean_PrecioOferta(self):
        precio_oferta = self.cleaned_data.get('PrecioOferta')
        esta_oferta = self.cleaned_data.get('EstaOferta')
        
        # Si está en oferta, el precio de oferta es obligatorio
        if esta_oferta and not precio_oferta:
            raise forms.ValidationError('El precio de oferta es obligatorio cuando el producto está en oferta')
        
        # Si no está vacío, limpiamos el formato
        if precio_oferta:
            # Removemos el símbolo de moneda y las comas
            precio_oferta = precio_oferta.replace('$', '').replace(',', '').strip()
            try:
                return float(precio_oferta)
            except ValueError:
                raise forms.ValidationError('Ingrese un precio válido')
        return None

    def clean_PrecioProducto(self):
        precio = self.cleaned_data.get('PrecioProducto')
        if precio:
            # Removemos el símbolo de moneda y las comas
            precio = precio.replace('$', '').replace(',', '').strip()
            try:
                return float(precio)
            except ValueError:
                raise forms.ValidationError('Ingrese un precio válido')
        raise forms.ValidationError('El precio es obligatorio')

    def clean(self):
        cleaned_data = super().clean()
        precio_normal = cleaned_data.get('PrecioProducto')
        precio_oferta = cleaned_data.get('PrecioOferta')
        esta_oferta = cleaned_data.get('EstaOferta')

        if esta_oferta and precio_oferta and precio_normal:
            if float(precio_oferta) >= float(precio_normal):
                raise forms.ValidationError(
                    'El precio de oferta debe ser menor que el precio normal'
                )
        
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super(ProductoForm, self).__init__(*args, **kwargs)
        # Configuración del widget de imagen
        if self.instance and self.instance.pk:
            self.fields['ImagenProducto'].widget = forms.FileInput(attrs={
                'class': 'form-control',
            })
        else:
            self.fields['ImagenProducto'].widget = forms.ClearableFileInput(attrs={
                'class': 'form-control',
            })

    def clean_ImagenProducto(self):
        imagen = self.cleaned_data.get('ImagenProducto')
        # Si no hay nueva imagen y es una actualización, mantener la imagen existente
        if not imagen and self.instance.pk:
            return self.instance.ImagenProducto
            
        if imagen and hasattr(imagen, 'name'):
            # Validar extensión
            ext = imagen.name.split('.')[-1].lower()
            valid_extensions = ['png', 'jpg', 'jpeg', 'webp']
            
            if ext not in valid_extensions:
                raise forms.ValidationError(
                    f'Solo se permiten archivos con extensión: {", ".join(valid_extensions)}'
                )
            
            if imagen.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError('El archivo no debe superar los 5MB')

        return imagen

    def save(self, commit=True):
        producto = super().save(commit=False)
        # Si no hay nueva imagen, mantener la existente
        if not self.cleaned_data.get('ImagenProducto') and self.instance.pk:
            producto.ImagenProducto = self.instance.ImagenProducto
        if commit:
            producto.save()
        return producto

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
    
class VeterinariaForm(forms.ModelForm):
    class Meta:
        model = Veterinaria
        fields = ['NombreVeterinaria', 'LocalidadVeterinaria', 'HorarioInicioVeterinaria', 'HorarioCierreVeterinaria', 'DisponibilidadVeterinaria', 'telefono', 'email']
        widgets = {
            'NombreVeterinaria': forms.TextInput(attrs={'class': 'form-control'}),
            'LocalidadVeterinaria': forms.TextInput(attrs={'class': 'form-control'}),
            'HorarioInicioVeterinaria': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'HorarioCierreVeterinaria': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'DisponibilidadVeterinaria': forms.Select(attrs={'class': 'form-select'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

class VeterinarioForm(forms.ModelForm):
    class Meta:
        model = Veterinario
        fields = ['usuario', 'veterinaria', 'especialidad', 'telefono', 'experiencia_años', 'horario_inicio', 'horario_fin', 'nombre_veterinario']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'veterinaria': forms.Select(attrs={'class': 'form-select'}),
            'especialidad': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'experiencia_años': forms.TextInput(attrs={'class': 'form-control'}),
            'horario_inicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'horario_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'nombre_veterinario': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }

    # Campos opcionales: Usuario y Veterinaria
    usuario = forms.ModelChoiceField(
        queryset=CustomUser.objects.all(), 
        required=False, 
        empty_label="Seleccione un usuario", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    veterinaria = forms.ModelChoiceField(
        queryset=Veterinaria.objects.all(), 
        required=False, 
        empty_label="Seleccione una veterinaria", 
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    # Validación personalizada para asegurarse de que si no se selecciona usuario, el nombre del veterinario debe ser proporcionado
    def clean(self):
        cleaned_data = super().clean()
        usuario = cleaned_data.get("usuario")
        nombre_veterinario = cleaned_data.get("nombre_veterinario")
        veterinaria = cleaned_data.get("veterinaria")

        # Si no se selecciona un usuario, nombre_veterinario debe ser obligatorio
        if not usuario and not nombre_veterinario:
            self.add_error('nombre_veterinario', 'Debe ingresar el nombre del veterinario si no selecciona un usuario.')

        # Si no se selecciona una veterinaria, esto también podría ser validado si es necesario
        if not veterinaria:
            self.add_error('veterinaria', 'Debe seleccionar una veterinaria.')

        return cleaned_data
class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['NombreServicio', 'TipoServicio', 'LocalidadServicio', 'HorarioInicioServicio', 'HorarioCierreServicio', 'DisponibilidadServicio', 'Precio']
        widgets = {
            'NombreServicio': forms.TextInput(attrs={'class': 'form-control'}),
            'TipoServicio': forms.Select(attrs={'class': 'form-select'}),
            'LocalidadServicio': forms.TextInput(attrs={'class': 'form-control'}),
            'HorarioInicioServicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'HorarioCierreServicio': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'DisponibilidadServicio': forms.Select(attrs={'class': 'form-select'}),
            'Precio': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class CitaVeterinariaForm(forms.ModelForm):
    class Meta:
        model = CitaVeterinaria
        fields = ['servicio', 'veterinaria', 'veterinario', 'fecha', 'hora', 'notas']
        widgets = {
            'servicio': forms.Select(attrs={'class': 'form-select'}),
            'veterinaria': forms.Select(attrs={'class': 'form-select'}),
            'veterinario': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hora': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notas': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    


