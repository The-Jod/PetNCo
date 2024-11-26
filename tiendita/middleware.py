from django.utils import timezone
from django.db.models import Q
from .models import DisponibilidadVeterinario
from django.http import HttpResponse
from django.db import connection

class LimpiarHorariosMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Limpiar horarios antes de procesar la solicitud
            ahora = timezone.now()
            DisponibilidadVeterinario.objects.filter(
                Fecha__lt=ahora.date()
            ).update(
                EstaDisponible=False,
                EstadoHorario='expirado'
            )
            
            response = self.get_response(request)
            return response
        except ConnectionAbortedError:
            connection.close()
            return HttpResponse(status=499)  # Client Closed Request 