from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image
import os
from io import BytesIO
from django.core.files.base import ContentFile
from decimal import Decimal
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import RegexValidator

# Definir la función de validación al principio del archivo
def validate_image_file_extension(value):
    if value:  # Verificar si hay un archivo
        ext = os.path.splitext(value.name)[1]
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if not ext.lower() in valid_extensions:
            raise ValidationError('Solo se permiten archivos JPG, PNG o WebP.')

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
    RutUsuario = models.IntegerField(unique=True)
    NombreUsuario = models.CharField(max_length=80, null=True, blank=True)
    ApellidoUsuario = models.CharField(max_length=80, null=True, blank=True)
    EmailUsuario = models.EmailField(max_length=128)
    
    telefono_validator = RegexValidator(
        regex=r'^\+56[0-9]{9}$',
        message='El número debe tener formato +56 seguido de 9 dígitos'
    )
    
    TelefonoUsuario = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        validators=[telefono_validator],
        help_text='Formato: +56 9 12345678'
    )
    
    DomicilioUsuario = models.CharField(max_length=200, null=True, blank=True)
    
    TIPO_ANIMAL_CHOICES = [
        (0.1, 'Gato'),
        (0.2, 'Perro'),
        (0.3, 'Ave'),
        (0.4, 'Hamster')
    ]
    
    TipoAnimal = models.FloatField(choices=TIPO_ANIMAL_CHOICES, null=True, blank=True)
    ImagenPerfil = models.ImageField(
        upload_to='perfiles/', 
        null=True, 
        blank=True,
        validators=[validate_image_file_extension]
    )
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'RutUsuario'
    REQUIRED_FIELDS = ['EmailUsuario']

    def __str__(self):
        return f"{self.NombreUsuario} {self.ApellidoUsuario}" if self.NombreUsuario else str(self.RutUsuario)

    def get_full_name(self):
        return f"{self.NombreUsuario} {self.ApellidoUsuario}"

    def get_short_name(self):
        return self.NombreUsuario

    def get_phone_without_prefix(self):
        if self.TelefonoUsuario and self.TelefonoUsuario.startswith('+56'):
            return self.TelefonoUsuario[3:]
        return self.TelefonoUsuario

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

#Sistema De Citas
class Veterinaria(models.Model):
    CodigoVeterinaria = models.AutoField(primary_key=True)
    NombreVeterinaria = models.CharField(max_length=100)
    LocalidadVeterinaria = models.CharField(max_length=100)
    HorarioInicioVeterinaria = models.TimeField()
    HorarioCierreVeterinaria = models.TimeField()
    # CalificacionVeterinaria = models.FloatField(
    #     default=0,
    #     validators=[
    #         models.MinValueValidator(0),
    #         models.MaxValueValidator(5)
    #     ]
    # )
    DisponibilidadVeterinaria = models.CharField(
        max_length=1,
        choices=[('S', 'Sí'), ('N', 'No')],
        default='S'
    )
    # TipoAnimal = models.FloatField(choices=CustomUser.TIPO_ANIMAL_CHOICES)
    # Nuevos campos
    telefono = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        verbose_name = 'Veterinaria'
        verbose_name_plural = 'Veterinarias'
        indexes = [
            models.Index(fields=['LocalidadVeterinaria']),
            # models.Index(fields=['TipoAnimal'])
        ]

    def __str__(self):
        return self.NombreVeterinaria


class Veterinario(models.Model):
      # Ya no es primary_key
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    veterinaria = models.ForeignKey(Veterinaria, on_delete=models.CASCADE, null=True, blank=True)
    especialidad = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True)
    experiencia_años = models.CharField(max_length=150)
    horario_inicio = models.TimeField(null=True, blank=True)
    horario_fin = models.TimeField(null=True, blank=True)
    nombre_veterinario = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        verbose_name = 'Veterinario'
        verbose_name_plural = 'Veterinarios'

    def __str__(self):
        if self.usuario:
            return f"Dr. {self.usuario.NombreUsuario}"
        if self.nombre_veterinario:
            return self.nombre_veterinario
        elif self.email:
            return self.email
        return "Veterinario sin nombre ni correo"


class Servicio(models.Model):
    TIPO_SERVICIO = [
        ('PELUQUERIA', 'Peluquería'),
        ('LIMPIEZA', 'Limpieza'),
        ('DENTAL', 'Limpieza Dental'),
        ('VACUNACION', 'Vacunación'),
    ]

    CodigoServicio = models.AutoField(primary_key=True)
    NombreServicio = models.CharField(max_length=100)
    TipoServicio = models.CharField(max_length=20, choices=TIPO_SERVICIO)
    LocalidadServicio = models.CharField(max_length=100)
    HorarioInicioServicio = models.TimeField()
    HorarioCierreServicio = models.TimeField()
    # CalificacionServicio = models.FloatField(
    #     default=0,
    #     validators=[
    #         models.MinValueValidator(0),
    #         models.MaxValueValidator(5)
    #     ]
    # )
    DisponibilidadServicio = models.CharField(
        max_length=1,
        choices=[('S', 'Sí'), ('N', 'No')],
        default='S'
    )
    # TipoAnimal = models.FloatField(choices=CustomUser.TIPO_ANIMAL_CHOICES)
    Precio = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'

    def __str__(self):
        return f"{self.NombreServicio} - {self.get_TipoServicio_display()}"


class CitaVeterinaria(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
    ]

    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='citas')
    servicio = models.CharField(max_length=255)
    veterinaria = models.ForeignKey('Veterinaria', on_delete=models.CASCADE)
    veterinario = models.ForeignKey('Veterinario', on_delete=models.CASCADE)
    fecha = models.DateField()
    hora = models.TimeField()
    notas = models.TextField(blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    class Meta:
        ordering = ['-fecha', '-hora']

    def __str__(self):
        return f"Cita {self.servicio} - {self.fecha} {self.hora} ({self.estado})"
