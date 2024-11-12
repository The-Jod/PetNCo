from django.db import models

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
    
class Usuario(models.Model):
    RutUsuario = models.IntegerField(primary_key=True)
    NombreUsuario = models.CharField(max_length=80)
    PasswordUsuario = models.CharField(max_length=20)
    EmailUsuario = models.CharField(max_length=128)
    DomicilioUsuario = models.CharField(max_length=128)
    TipoAnimal = models.FloatField()

    def __str__(self):
        return self.NombreUsuario
    
class Veterinaria(models.Model):
    CodigoVeterinaria = models.IntegerField(primary_key=True)
    NombreVeterinaria = models.CharField(max_length=100)
    LocalidadVeterinaria = models.CharField(max_length=100)
    HorarioInicioVeterinaria = models.DateTimeField()
    HorarioCierreVeterinaria = models.DateTimeField()
    CalificacionVeterinaria = models.FloatField()
    DisponibilidadVeterinaria = models.CharField(max_length=1) 
    TipoAnimal = models.FloatField()
    RutUsuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)

    def __str__(self):
        return self.NombreVeterinaria
    
