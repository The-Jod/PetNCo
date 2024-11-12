from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

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
class Producto(models.Model):
    SKUProducto = models.IntegerField(primary_key=True)
    NombreProducto = models.CharField(max_length=128)
    StockProducto = models.IntegerField()
    PrecioProducto = models.FloatField()
    PrecioOferta = models.FloatField()
    EstaOferta = models.BooleanField(default=False)
    DescripcionProducto = models.CharField(max_length=500)

    # No se imaginan lo duro que fue averiguar esta wea
    CATEGORIAS = [
        (0.1, 'Alimentos'),
        (0.2, 'Accesorios'),
        (0.3, 'Juguetes'),
        (0.4, 'Camas y rascadores')
    ]
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
    