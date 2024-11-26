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
from django.core.validators import (
    RegexValidator, 
    MaxValueValidator, 
    MinValueValidator
)
import re
from django.db.models import Q
from django.db.models import Avg

# Definir la función de validación al principio del archivo
def validate_image_file_extension(value):
    ext = os.path.splitext(value.name)[1]
    valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    if not ext.lower() in valid_extensions:
        raise ValidationError('Formato de archivo no soportado.')

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
    is_veterinario = models.BooleanField(default=False)
    is_comerciante = models.BooleanField(default=False)

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


# Productos
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
    ImagenProducto = models.ImageField(
        upload_to='productos/',
        validators=[validate_image_file_extension],
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        # Si hay una imagen nueva, asegurarse de que solo se guarde una versión
        if self.ImagenProducto:
            # Mantener solo el formato original
            self.ImagenProducto.name = re.sub(r'\.webp$', '', self.ImagenProducto.name)
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
    
# Ordenes
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
        CustomUser,
        on_delete=models.CASCADE,
        null=False,
        blank=False
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

class PerfilVeterinario(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_veterinario'
    )
    NombreCompletoVeterinario = models.CharField(
        max_length=200,
        verbose_name="Nombre Completo",
        help_text="Ingrese su nombre completo incluyendo títulos (ej: Dr. Juan Pérez González)"
    )
    EmailVeterinario = models.EmailField(
        verbose_name="Correo Electrónico",
        unique=True
    )
    
    TelefonoVeterinario = models.BigIntegerField(
        verbose_name="Teléfono",
        help_text="Ingrese los 9 dígitos de su número celular",
        validators=[
            MinValueValidator(900000000, message="El número debe tener 9 dígitos"),
            MaxValueValidator(999999999, message="El número debe tener 9 dígitos")
        ],
        null=True,
        blank=True
    )
    
    Especialidad = models.CharField(
        max_length=100,
        verbose_name="Especialidad"
    )
    
    NumeroRegistro = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Número de Registro"
    )
    
    Descripcion = models.TextField(
        verbose_name="Descripción Profesional",
        help_text="Describa su experiencia y servicios principales",
        default="Sin descripción disponible",
        null=True,
        blank=True
    )
    
    ImagenPerfil = models.ImageField(
        upload_to='perfiles_veterinarios/',
        null=True,
        blank=True,
        validators=[validate_image_file_extension],
        verbose_name="Foto de Perfil"
    )
    
    # Campos de ubicación
    Ubicacion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Dirección",
        help_text="Dirección donde atiende (puede ser editada posteriormente)"
    )
    
    MostrarUbicacion = models.BooleanField(
        default=True,
        verbose_name="Mostrar ubicación públicamente"
    )
    
    Latitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Se autocompletará al ingresar la dirección"
    )
    
    Longitud = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Se autocompletará al ingresar la dirección"
    )
    
    EstaActivo = models.BooleanField(
        default=True,
        verbose_name="Perfil Activo"
    )

    class Meta:
        verbose_name = "Perfil de Veterinario"
        verbose_name_plural = "Perfiles de Veterinarios"
        ordering = ['NombreCompletoVeterinario']

    def __str__(self):
        return f"Dr(a). {self.NombreCompletoVeterinario}"

    def get_phone_formatted(self):
        """Retorna el número de teléfono formateado como +56 9 XXXX XXXX"""
        phone_str = str(self.TelefonoVeterinario)
        return f"+56 9 {phone_str[1:5]} {phone_str[5:]}"

    def save(self, *args, **kwargs):
        # Aquí podrías agregar lógica para geocodificar la dirección
        # y actualizar Latitud/Longitud automáticamente
        super().save(*args, **kwargs)

    @property
    def promedio_calificaciones(self):
        resenas = self.resenas.all()
        if not resenas:
            return 0
        return resenas.aggregate(Avg('Calificacion'))['Calificacion__avg'] or 0
    
    @property
    def total_resenas(self):
        return self.resenas.count()
    
    def distribucion_calificaciones(self):
        """Retorna un diccionario con la distribución de calificaciones"""
        return {
            i: self.resenas.filter(Calificacion=i).count()
            for i in range(1, 6)
        }

    @property
    def horarios_atencion(self):
        """Alias para disponibilidades para mantener consistencia en templates"""
        return self.disponibilidades.filter(
            Fecha__gte=timezone.now().date(),
            EstaDisponible=True
        ).order_by('Fecha', 'HorarioInicio')

class ServicioBase(models.Model):
    TIPO_CHOICES = [
        ('CONSULTA', 'Consulta General'),
        ('VACUNA', 'Vacunación'),
        ('CIRUGIA', 'Cirugía'),
        ('EMERGENCIA', 'Emergencia'),
        ('GROOMING', 'Peluquería'),
        ('DENTAL', 'Limpieza Dental'),
        ('ESPECIALIDAD', 'Consulta Especialidad')
    ]

    CodigoServicio = models.AutoField(primary_key=True)
    NombreServicio = models.CharField(max_length=100)
    TipoServicio = models.CharField(max_length=50, choices=TIPO_CHOICES)
    EstaActivo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Servicio Base'
        verbose_name_plural = 'Servicios Base'
        ordering = ['TipoServicio', 'NombreServicio']
        db_table = 'ServicioBase'

    def __str__(self):
        return f"{self.NombreServicio} ({self.get_TipoServicio_display()})"

class ServicioPersonalizado(models.Model):
    veterinario = models.ForeignKey(
        'PerfilVeterinario', 
        on_delete=models.CASCADE,
        related_name='servicios_personalizados'
    )
    servicio_base = models.ForeignKey(
        ServicioBase, 
        on_delete=models.CASCADE,
        related_name='personalizaciones'
    )
    Precio = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Precio del servicio",
        default=0
    )
    EstaActivo = models.BooleanField(default=True)
    Notas = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Servicio Personalizado'
        verbose_name_plural = 'Servicios Personalizados'
        unique_together = ['veterinario', 'servicio_base']

    def __str__(self):
        return f"{self.servicio_base.NombreServicio} - Dr(a). {self.veterinario.NombreVeterinario}"

class DisponibilidadVeterinario(models.Model):
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('reservado', 'Reservado'),
        ('expirado', 'Expirado'),
        ('cancelado', 'Cancelado')
    ]
    
    veterinario = models.ForeignKey(
        PerfilVeterinario,
        on_delete=models.CASCADE,
        related_name='disponibilidades'
    )
    Fecha = models.DateField()
    HorarioInicio = models.TimeField()
    HorarioFin = models.TimeField()
    EstaDisponible = models.BooleanField(default=True)
    FechaCreacion = models.DateTimeField(auto_now_add=True)
    UltimaActualizacion = models.DateTimeField(auto_now=True)
    EstadoHorario = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='disponible'
    )
    
    class Meta:
        ordering = ['Fecha', 'HorarioInicio']
        constraints = [
            models.UniqueConstraint(
                fields=['veterinario', 'Fecha', 'HorarioInicio'],
                name='unique_veterinario_fecha_inicio'
            )
        ]
        indexes = [
            models.Index(fields=['Fecha', 'HorarioInicio']),
            models.Index(fields=['EstaDisponible', 'EstadoHorario']),
            models.Index(fields=['Fecha', 'EstaDisponible']),
            models.Index(fields=['veterinario', 'Fecha']),
            models.Index(fields=['EstadoHorario']),
        ]

    def tiene_conflicto(self):
        """Verifica si hay conflictos con otros horarios"""
        solapados = DisponibilidadVeterinario.objects.filter(
            veterinario=self.veterinario,
            Fecha=self.Fecha,
            EstaDisponible=True
        ).filter(
            Q(HorarioInicio__lt=self.HorarioFin, HorarioFin__gt=self.HorarioInicio) |
            Q(HorarioInicio=self.HorarioInicio, HorarioFin=self.HorarioFin)
        )
        
        if self.pk:  # Si estamos actualizando, excluimos el registro actual
            solapados = solapados.exclude(pk=self.pk)
            
        return solapados.exists()

    def clean(self):
        super().clean()
        
        # Validaciones existentes de fecha y hora
        ahora = timezone.localtime(timezone.now())
        hoy = ahora.date()
        hora_actual = ahora.time()
        
        if self.Fecha < hoy:
            raise ValidationError('No se pueden crear horarios en fechas pasadas')
        
        if self.Fecha == hoy:
            hora_inicio = datetime.combine(hoy, self.HorarioInicio)
            hora_actual = datetime.combine(hoy, hora_actual)
            hora_actual = hora_actual - timedelta(minutes=5)
            
            if hora_inicio.time() <= hora_actual.time():
                raise ValidationError({
                    'HorarioInicio': 'La hora de inicio debe ser posterior a la hora actual'
                })
        
        if self.HorarioInicio >= self.HorarioFin:
            raise ValidationError({
                'HorarioInicio': 'La hora de inicio debe ser anterior a la hora de fin'
            })
        
        # Validación de duración
        inicio = datetime.combine(datetime.today(), self.HorarioInicio)
        fin = datetime.combine(datetime.today(), self.HorarioFin)
        diferencia = (fin - inicio).total_seconds() / 60
        
        if diferencia < 60:
            raise ValidationError({
                'HorarioInicio': 'El horario debe tener como mínimo una hora de duración'
            })
            
        if diferencia > 720:  # 12 horas en minutos
            raise ValidationError({
                'HorarioInicio': 'El horario no puede exceder las 12 horas'
            })
        
        # Verificar conflictos usando el nuevo método
        if self.tiene_conflicto():
            raise ValidationError('Este horario se solapa con otro existente')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class ResenaVeterinario(models.Model):
    veterinario = models.ForeignKey(
        'PerfilVeterinario',
        on_delete=models.CASCADE,
        related_name='resenas'
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='resenas_veterinarios'
    )
    Calificacion = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    Comentario = models.TextField()
    RespuestaVeterinario = models.TextField(
        null=True, 
        blank=True,
        verbose_name="Respuesta del veterinario"
    )
    FechaCreacion = models.DateTimeField(auto_now_add=True)
    FechaRespuesta = models.DateTimeField(
        null=True, 
        blank=True
    )
    
    class Meta:
        verbose_name = "Reseña de Veterinario"
        verbose_name_plural = "Reseñas de Veterinarios"
        unique_together = ['veterinario', 'usuario']
        ordering = ['-FechaCreacion']

    def __str__(self):
        return f"Reseña de {self.usuario} para {self.veterinario}"

class CitaVeterinaria(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
        ('completada', 'Completada')
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='citas'
    )
    veterinario = models.ForeignKey(
        'PerfilVeterinario',
        on_delete=models.CASCADE,
        related_name='citas'
    )
    servicios = models.ManyToManyField(
        'ServicioPersonalizado',
        related_name='citas'
    )
    horario = models.ForeignKey(
        'DisponibilidadVeterinario',
        on_delete=models.SET_NULL,
        null=True
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    notas = models.TextField(blank=True, null=True)
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    evento_google_usuario = models.CharField(max_length=255, blank=True, null=True)
    evento_google_veterinario = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        ordering = ['-fecha', '-hora_inicio']
        
    def __str__(self):
        return f"Cita {self.id} - {self.usuario} con {self.veterinario}"