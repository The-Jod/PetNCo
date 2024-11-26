# Standard library imports

from datetime import datetime, timedelta, date
import re

# Django imports
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils import timezone
import os

# Local application imports
from .models import Producto, CustomUser, DisponibilidadVeterinario

def validar_rut_chileno(rut):
    # Limpia el RUT de puntos y guión
    rut = rut.replace(".", "").replace("-", "").upper()
    
    # Verifica el formato básico
    if not re.match(r'^[0-9]{7,8}[0-9K]$', rut):
        raise ValidationError('Formato de RUT inválido')
    
    # Separa el RUT del dígito verificador
    rut_sin_dv = rut[:-1]
    dv = rut[-1]
    
    # Calcula el dígito verificador
    multiplicador = 2
    suma = 0
    for d in reversed(rut_sin_dv):
        suma += int(d) * multiplicador
        multiplicador = multiplicador + 1 if multiplicador < 7 else 2
    
    dv_calculado = 11 - (suma % 11)
    dv_esperado = {10: 'K', 11: '0'}.get(dv_calculado, str(dv_calculado))
    
    # Verifica que el dígito verificador sea correcto
    if dv != dv_esperado:
        raise ValidationError('RUT inválido')
    
    # Convierte K a 11 y retorna solo números
    return int(rut_sin_dv + ('11' if dv == 'K' else dv))

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
                regex=r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
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
    RutUsuario = forms.CharField(
        label='RUT',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ejemplo: 12.345.678-9'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['RutUsuario', 'EmailUsuario', 'password1', 'password2']
        widgets = {
            'EmailUsuario': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Correo Electrónico'
            }),
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
        
    def clean_RutUsuario(self):
        rut = self.cleaned_data.get('RutUsuario')
        try:
            rut_limpio = validar_rut_chileno(rut)
            return rut_limpio
        except ValidationError as e:
            raise forms.ValidationError('RUT inválido. Verifique el formato y el dígito verificador.')

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        label='RUT',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu RUT'
        })
    )
    
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña'
        })
    )

    error_messages = {
        'invalid_login': "RUT o contraseña incorrectos",
        'inactive': 'Esta cuenta está inactiva.',
        'invalid_rut': 'El RUT ingresado no es válido.'
    }

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            try:
                # Limpia y valida el RUT
                username = username.replace('.', '').replace('-', '').upper()
                rut_limpio = validar_rut_chileno(username)
                
                # Intenta autenticar al usuario
                self.user_cache = authenticate(
                    self.request,
                    username=str(rut_limpio),
                    password=password
                )
                
                if self.user_cache is None:
                    # Cambio en la forma de lanzar el error
                    self.add_error('password', self.error_messages['invalid_login'])
                elif not self.user_cache.is_active:
                    raise forms.ValidationError(
                        self.error_messages['inactive'],
                        code='inactive'
                    )
            except ValidationError as e:
                if 'RUT inválido' in str(e) or 'Formato de RUT inválido' in str(e):
                    self.add_error('username', self.error_messages['invalid_rut'])
                else:
                    self.add_error('password', str(e))
                raise

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        if not user.is_active:
            raise forms.ValidationError(
                self.error_messages['inactive'],
                code='inactive',
            )

class CambiarPasswordForm(forms.Form):
    password_actual = forms.CharField(
        label="Contraseña actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su contraseña actual'
        })
    )
    password_nuevo = forms.CharField(
        label="Nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingrese su nueva contraseña'
        })
    )
    password_confirmacion = forms.CharField(
        label="Confirmar nueva contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirme su nueva contraseña'
        })
    )

    def clean_password_nuevo(self):
        password = self.cleaned_data.get('password_nuevo')
        
        # Validar longitud mínima
        if len(password) < 8:
            raise forms.ValidationError(
                'La contraseña debe tener al menos 8 caracteres'
            )
        
        # Validar que contenga al menos un número
        if not any(char.isdigit() for char in password):
            raise forms.ValidationError(
                'La contraseña debe contener al menos un número'
            )
        
        return password

    def clean(self):
        cleaned_data = super().clean()
        password_nuevo = cleaned_data.get('password_nuevo')
        password_confirmacion = cleaned_data.get('password_confirmacion')

        if password_nuevo and password_confirmacion:
            if password_nuevo != password_confirmacion:
                raise forms.ValidationError('Las contraseñas nuevas no coinciden')
        return cleaned_data

class DisponibilidadForm(forms.ModelForm):
    class Meta:
        model = DisponibilidadVeterinario
        fields = ['Fecha', 'HorarioInicio', 'HorarioFin']

    def clean(self):
        cleaned_data = super().clean()
        inicio = cleaned_data.get('HorarioInicio')
        fin = cleaned_data.get('HorarioFin')
        fecha = cleaned_data.get('Fecha')

        if all([inicio, fin, fecha]):
            # Validar que la fecha no sea pasada
            if fecha < timezone.now().date():
                raise ValidationError('No se pueden crear horarios en fechas pasadas')
            
            # Validar que el fin sea después del inicio
            if fin <= inicio:
                raise ValidationError('La hora de fin debe ser posterior a la hora de inicio')
            
            # Validar duración mínima (ejemplo: 30 minutos)
            duracion = datetime.combine(fecha, fin) - datetime.combine(fecha, inicio)
            if duracion.total_seconds() < 1800:  # 30 minutos
                raise ValidationError('El horario debe tener una duración mínima de 30 minutos')

        return cleaned_data

