from django import forms
from django.core.validators import RegexValidator
from .models import Producto
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Producto, CustomUser


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
    
    
    ImagenProducto = forms.ImageField (
        required=False,  # Opcional ya que es precio de oferta
        widget=forms.TextInput(attrs={
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
    # Busca la imagen de producto, Fue un parto lograr que funcionara, xfavor no le muevan.
        if self.instance and self.instance.pk:
            self.fields['ImagenProducto'].widget = forms.FileInput(attrs={
                'class': 'form-control',
            })
        else:
            self.fields['ImagenProducto'].widget = forms.ClearableFileInput(attrs={
            'class': 'form-control',
        })
    
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
    

class LoginForm(forms.Form):
    RutUsuario = forms.IntegerField(label="RUT Usuario")
    password = forms.CharField(widget=forms.PasswordInput)