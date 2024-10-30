from django.db import models

# Create your models here.
class Producto(models.Model):
    SKUProducto = models.IntegerField(primary_key=True)
    NombreProducto = models.CharField(max_length=128)
    StockProducto = models.IntegerField()
    PrecioProducto = models.FloatField()
    DescripcionProducto = models.CharField(max_length=500)
    TipoAnimal = models.FloatField()
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
    
