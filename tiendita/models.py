from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
from django.contrib.auth.models import User
from django.conf import settings

# Manager personalizado para manejar la creación de usuarios
class CustomUserManager(BaseUserManager):
    def create_user(self, RutUsuario, password=None, **extra_fields):
        if not RutUsuario:
            raise ValueError('El RUT es obligatorio')

        user = self.model(RutUsuario=RutUsuario, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


# Modelo personalizado de Usuario
class CustomUser(AbstractBaseUser, PermissionsMixin):
    RutUsuario = models.IntegerField(unique=True)  # Reemplazamos username por RUT
    NombreUsuario = models.CharField(max_length=80, null=True, blank=True)
    EmailUsuario = models.EmailField(max_length=128, )
    DomicilioUsuario = models.CharField(max_length=200, null=True, blank=True)
    TipoAnimal = models.FloatField(blank=True,null=True)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'RutUsuario'  # Este será el campo de inicio de sesión
    REQUIRED_FIELDS = ['EmailUsuario']  # Otros campos requeridos además de la contraseña

    def __str__(self):
        return str(self.RutUsuario)

# Create your models here.
from django.db import models

class Producto(models.Model):
    SKUProducto = models.IntegerField(primary_key=True)
    NombreProducto = models.CharField(max_length=128)
    StockProducto = models.IntegerField()
    PrecioProducto = models.DecimalField(max_digits=10, decimal_places=2)
    PrecioOferta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    EstaOferta = models.BooleanField(default=False)
    DescripcionProducto = models.CharField(max_length=500)

    CATEGORIAS = [
        (0.1, 'Alimentos'),
        (0.2, 'Accesorios'),
        (0.3, 'Juguetes'),
        (0.4, 'Camas y rascadores')
    ]

    # Diccionario de colores para cada categoría
    COLORES_CATEGORIAS = {
        0.1: '#4A90E2',  # Rojo suave para Alimentos
        0.2: '#8E44AD',  # Turquesa para Accesorios
        0.3: '#2ECC71',  # Amarillo para Juguetes
        0.4: '#BDC3C7'   # Gris para Camas y rascadores
    }

    TIPO_ANIMAL = [
        (0.1, 'Gato'),
        (0.2, 'Perro'),
        (0.3, 'Ave'),
        (0.4, 'Hamster')
    ]



    CategoriaProducto = models.FloatField(choices=CATEGORIAS)
    TipoAnimal = models.FloatField(choices=TIPO_ANIMAL)
    ImagenProducto = models.ImageField(upload_to='productos/', null=True, blank=True)

    def save(self, *args, **kwargs):
        # Primero guardamos el modelo para tener el ID
        super().save(*args, **kwargs)
        
        # Si hay una imagen, la procesamos
        if self.ImagenProducto:
            try:
                # Abrir la imagen
                img = Image.open(self.ImagenProducto.path)
                
                # Convertir a RGB si es necesario
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Redimensionar si es muy grande (manteniendo proporción)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size, Image.Resampling.LANCZOS)
                
                # Crear el nombre del archivo WebP
                nombre_base = os.path.splitext(os.path.basename(self.ImagenProducto.name))[0]
                nuevo_nombre = f"{nombre_base}.webp"
                
                # Guardar como WebP
                buffer = BytesIO()
                img.save(buffer, 'WebP', quality=85, optimize=True)
                
                # Actualizar el campo de imagen
                self.ImagenProducto.save(
                    nuevo_nombre,
                    ContentFile(buffer.getvalue()),
                    save=False
                )
                
                # Limpiar el buffer
                buffer.close()
                
            except Exception as e:
                print(f"Error procesando imagen del producto {self.SKUProducto}: {e}")
        
        super().save(*args, **kwargs)

    def __str__(self):
        return self.NombreProducto

    @property
    def porcentaje_descuento(self):
        if self.PrecioOferta and self.PrecioProducto:
            descuento = (self.PrecioProducto - self.PrecioOferta) * 100 / self.PrecioProducto
            return round(descuento, 2)
        return 0

    def get_color_categoria(self):
        """Retorna el color hexadecimal asociado a la categoría del producto"""
        return self.COLORES_CATEGORIAS.get(self.CategoriaProducto, '#CCCCCC')  # Gris por defecto

    def get_color_animal(self):
        """Retorna el color hexadecimal asociado al tipo de animal"""
        return self.COLORES_ANIMALES.get(self.TipoAnimal, '#CCCCCC')  # Gris por defecto
    
class Orden(models.Model):
    id = models.AutoField(primary_key=True)
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagado', 'Pagado'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ordenes'
    )
    NombreCliente = models.CharField(max_length=200, null=True, blank=True)
    ApellidoCliente = models.CharField(max_length=200, null=True, blank=True)
    EmailCliente = models.EmailField(null=True, blank=True)
    TelefonoCliente = models.CharField(max_length=20, null=True, blank=True)
    DireccionCliente = models.TextField(null=True, blank=True)
    FechaOrden = models.DateTimeField(auto_now_add=True)
    EstadoOrden = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente'
    )
    TotalOrden = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True
    )
    CostoEnvio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True
    )
    TokenWebpay = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return f"Orden #{self.id} - {self.NombreCliente} {self.ApellidoCliente}"

class OrdenItem(models.Model):
    id = models.AutoField(primary_key=True)
    orden = models.ForeignKey(Orden, related_name='items', on_delete=models.CASCADE)
    SKUProducto = models.ForeignKey('Producto', on_delete=models.SET_NULL, null=True)
    NombreProducto = models.CharField(max_length=200, null=True, blank=True)
    PrecioProducto = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True
    )
    CantidadProducto = models.IntegerField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.CantidadProducto}x {self.NombreProducto}"

class Veterinaria(models.Model):
    CodigoVeterinaria = models.IntegerField(primary_key=True)
    NombreVeterinaria = models.CharField(max_length=100)
    LocalidadVeterinaria = models.CharField(max_length=100)
    HorarioInicioVeterinaria = models.DateTimeField()
    HorarioCierreVeterinaria = models.DateTimeField()
    CalificacionVeterinaria = models.FloatField()
    DisponibilidadVeterinaria = models.CharField(max_length=1) 
    TipoAnimal = models.FloatField()

    def __str__(self):
        return self.NombreVeterinaria
    