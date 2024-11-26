from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Q
from .models import DisponibilidadVeterinario, Cita

@receiver([pre_save, post_save], sender=DisponibilidadVeterinario)
def gestionar_disponibilidad(sender, instance, **kwargs):
    """Gestiona automáticamente la disponibilidad de horarios"""
    ahora = timezone.now()
    
    # Actualizar horarios pasados
    DisponibilidadVeterinario.objects.filter(
        Q(Fecha__lt=ahora.date()) |
        Q(Fecha=ahora.date(), HorarioInicio__lt=ahora.time())
    ).update(
        EstaDisponible=False,
        EstadoHorario='expirado'
    )
    
    # Verificar el horario actual
    if instance.Fecha < ahora.date():
        instance.EstaDisponible = False
        instance.EstadoHorario = 'expirado'
    elif instance.Fecha == ahora.date() and instance.HorarioInicio < ahora.time():
        instance.EstaDisponible = False
        instance.EstadoHorario = 'expirado'

@receiver(post_save, sender=Cita)
def actualizar_disponibilidad_post_cita(sender, instance, created, **kwargs):
    """Actualiza la disponibilidad después de crear/modificar una cita"""
    if created or instance.Estado == 'confirmada':
        DisponibilidadVeterinario.objects.filter(
            id=instance.horario.id
        ).update(
            EstaDisponible=False,
            EstadoHorario='reservado'
        ) 