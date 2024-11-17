from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
from django.contrib.auth.models import User

from django.utils import timezone

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
    CodigoUnicoOrden = models.IntegerField(primary_key=True)
    SKUProducto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    NombreProducto = models.CharField(max_length=128)
    RutUsuario = models.IntegerField()
    EmailUsuario = models.CharField(max_length=128)
    DomicilioUsuario = models.CharField(max_length=128)
    FechaEstimadaOrden = models.DateField()

    def __str__(self):
        return f"Orden {self.CodigoUnicoOrden} - {self.NombreProducto}"
#
#
#
#

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
    usuario = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    veterinaria = models.ForeignKey(Veterinaria, on_delete=models.CASCADE)
    especialidad = models.CharField(max_length=100)
    # color = models.CharField(max_length=7, default="#2196F3")
    # Nuevos campos
    telefono = models.CharField(max_length=15, blank=True)
    experiencia_años = models.CharField(max_length=150)
    horario_inicio = models.TimeField(null=True, blank=True)
    horario_fin = models.TimeField(null=True, blank=True)

    class Meta:
        verbose_name = 'Veterinario'
        verbose_name_plural = 'Veterinarios'
        indexes = [
            models.Index(fields=['especialidad'])
        ]

    def __str__(self):
        return f"Dr. {self.usuario.NombreUsuario}"

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
