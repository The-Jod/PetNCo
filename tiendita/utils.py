from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def enviar_correo_orden(orden):
    """
    Envía el correo de confirmación de la orden
    """
    try:
        # Contexto para el template
        context = {
            'orden': orden,
            'items': orden.items.all(),
            'subtotal': orden.TotalOrden - orden.CostoEnvio,
        }
        
        # Renderizar el template HTML
        html_message = render_to_string('emails/confirmacion_orden.html', context)
        plain_message = strip_tags(html_message)  # Versión texto plano
        
        # Enviar el correo
        send_mail(
            subject=f'Confirmación de Orden #{orden.id} - PetShop',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[orden.EmailCliente],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Correo de confirmación enviado para orden #{orden.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error enviando correo de confirmación para orden #{orden.id}: {str(e)}")
        return False