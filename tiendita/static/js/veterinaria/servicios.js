// Función para actualizar precio personalizado
async function actualizarServicioPersonalizado(servicioId, precio, estaActivo = true, notas = '') {
    try {
        const response = await fetch('/api/servicios/personalizado/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                servicio_id: servicioId,
                precio: precio,
                esta_activo: estaActivo,
                notas: notas
            })
        });

        const data = await response.json();
        if (data.success) {
            Swal.fire('¡Éxito!', 'Servicio actualizado correctamente', 'success');
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        Swal.fire('Error', error.message, 'error');
    }
}

// Inicializar eventos
document.addEventListener('DOMContentLoaded', function() {
    // Manejar edición de precios
    document.querySelectorAll('.editar-precio').forEach(btn => {
        btn.addEventListener('click', function() {
            const servicioId = this.dataset.servicio;
            const inputPrecio = document.querySelector(`input[data-servicio="${servicioId}"]`);
            inputPrecio.disabled = !inputPrecio.disabled;
            
            if (!inputPrecio.disabled) {
                inputPrecio.focus();
            }
        });
    });

    // Manejar cambios en precios
    document.querySelectorAll('.precio-personalizado').forEach(input => {
        input.addEventListener('change', function() {
            const servicioId = this.dataset.servicio;
            const precio = this.value;
            actualizarServicioPersonalizado(servicioId, precio);
        });
    });
}); 