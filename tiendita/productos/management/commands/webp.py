from django.core.management.base import BaseCommand
from productos.models import Producto
from PIL import Image
import os

class Command(BaseCommand):
    help = 'Convierte todas las imágenes existentes a formato WebP'

    def handle(self, *args, **kwargs):
        productos = Producto.objects.all()
        for producto in productos:
            if producto.ImagenProducto:
                try:
                    img = Image.open(producto.ImagenProducto.path)
                    webp_path = os.path.splitext(producto.ImagenProducto.path)[0] + '.webp'
                    img.save(webp_path, 'WebP', quality=85)
                    
                    # Actualizar el campo de imagen
                    webp_name = os.path.splitext(producto.ImagenProducto.name)[0] + '.webp'
                    os.remove(producto.ImagenProducto.path)
                    producto.ImagenProducto.name = webp_name
                    producto.save(update_fields=['ImagenProducto'])
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'Convertida imagen de producto {producto.SKUProducto}')
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error convirtiendo imagen de producto {producto.SKUProducto}: {e}')
                    ) 