document.addEventListener('DOMContentLoaded', function() {
    // Elementos del formulario
    const agendarForm = document.getElementById('agendarForm');
    const servicioSelect = agendarForm.querySelector('[name="servicio"]');
    const fechaInput = agendarForm.querySelector('[name="fecha"]');
    const horarioSelect = agendarForm.querySelector('[name="horario"]');
    
    // Manejar click en botón de agendar
    document.querySelectorAll('.btn-agendar').forEach(btn => {
        btn.addEventListener('click', async function() {
            const vetId = this.dataset.vetId;
            
            // Cargar servicios del veterinario
            try {
                const response = await fetch(`/api/veterinarios/${vetId}/servicios/`);
                const servicios = await response.json();
                
                // Actualizar select de servicios
                servicioSelect.innerHTML = '<option value="">Seleccione un servicio</option>';
                servicios.forEach(servicio => {
                    servicioSelect.innerHTML += `
                        <option value="${servicio.id}">${servicio.nombre} - $${servicio.precio}</option>
                    `;
                });
            } catch (error) {
                Swal.fire('Error', 'No se pudieron cargar los servicios', 'error');
            }
        });
    });

    // Actualizar horarios disponibles cuando cambie la fecha
    fechaInput.addEventListener('change', async function() {
        const vetId = document.querySelector('.btn-agendar').dataset.vetId;
        const servicioId = servicioSelect.value;
        const fecha = this.value;

        if (!servicioId) {
            Swal.fire('Error', 'Primero seleccione un servicio', 'warning');
            return;
        }

        try {
            const response = await fetch(
                `/api/veterinarios/${vetId}/disponibilidad/?fecha=${fecha}&servicio=${servicioId}`
            );
            const horarios = await response.json();

            // Actualizar select de horarios
            horarioSelect.innerHTML = '<option value="">Seleccione un horario</option>';
            horarios.forEach(horario => {
                horarioSelect.innerHTML += `
                    <option value="${horario.id}">${horario.hora_inicio} - ${horario.hora_fin}</option>
                `;
            });
        } catch (error) {
            Swal.fire('Error', 'No se pudieron cargar los horarios disponibles', 'error');
        }
    });

    // Manejar confirmación de cita
    document.getElementById('confirmarCita').addEventListener('click', async function() {
        const vetId = document.querySelector('.btn-agendar').dataset.vetId;
        const formData = new FormData(agendarForm);

        try {
            const response = await fetch('/api/citas/agendar/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    veterinario_id: vetId,
                    servicio_id: formData.get('servicio'),
                    fecha: formData.get('fecha'),
                    horario_id: formData.get('horario')
                })
            });

            if (response.ok) {
                Swal.fire('¡Éxito!', 'Tu cita ha sido agendada', 'success')
                    .then(() => {
                        $('#agendarModal').modal('hide');
                        agendarForm.reset();
                    });
            } else {
                throw new Error('Error al agendar la cita');
            }
        } catch (error) {
            Swal.fire('Error', error.message, 'error');
        }
    });
}); 