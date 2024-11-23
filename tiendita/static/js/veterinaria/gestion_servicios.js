document.addEventListener('DOMContentLoaded', function() {
    // Formulario de crear servicio
    const formCrearServicio = document.getElementById('formCrearServicio');
    if (formCrearServicio) {
        formCrearServicio.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            try {
                const response = await fetch('/api/servicios/gestion/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        accion: 'crear',
                        nombre: formData.get('nombre'),
                        tipo: formData.get('tipo')
                    })
                });

                const data = await response.json();
                if (data.success) {
                    Swal.fire({
                        title: '¡Éxito!',
                        text: 'Servicio creado correctamente',
                        icon: 'success',
                        confirmButtonText: 'OK'
                    }).then(() => {
                        location.reload();
                    });
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                Swal.fire('Error', error.message, 'error');
            }
        });
    }

    // Formulario de editar servicio
    const formEditarServicio = document.getElementById('formEditarServicio');
    if (formEditarServicio) {
        formEditarServicio.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            try {
                const response = await fetch('/api/servicios/gestion/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        accion: 'editar',
                        servicio_id: formData.get('servicio_id'),
                        nombre: formData.get('nombre'),
                        tipo: formData.get('tipo')
                    })
                });

                const data = await response.json();
                if (data.success) {
                    Swal.fire({
                        title: '¡Éxito!',
                        text: 'Servicio actualizado correctamente',
                        icon: 'success',
                        confirmButtonText: 'OK'
                    }).then(() => {
                        location.reload();
                    });
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                Swal.fire('Error', error.message, 'error');
            }
        });
    }

    // Cargar datos para editar
    document.querySelectorAll('.editar-servicio').forEach(btn => {
        btn.addEventListener('click', async function() {
            const servicioId = this.dataset.servicio;
            try {
                const response = await fetch(`/api/servicios/gestion/?id=${servicioId}`);
                const data = await response.json();
                
                if (data.servicio) {
                    const form = document.getElementById('formEditarServicio');
                    form.querySelector('[name=servicio_id]').value = data.servicio.id;
                    form.querySelector('[name=nombre]').value = data.servicio.nombre;
                    form.querySelector('[name=tipo]').value = data.servicio.tipo;
                } else {
                    throw new Error('No se pudo cargar la información del servicio');
                }
            } catch (error) {
                Swal.fire('Error', error.message, 'error');
            }
        });
    });

    // Toggle estado
    document.querySelectorAll('.toggle-estado').forEach(toggle => {
        toggle.addEventListener('change', async function() {
            const servicioId = this.dataset.servicio;
            const estado = this.checked;
            
            try {
                const response = await fetch('/api/servicios/gestion/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        accion: 'toggle_estado',
                        servicio_id: servicioId,
                        estado: estado
                    })
                });

                const data = await response.json();
                if (data.success) {
                    Swal.fire({
                        title: '¡Estado actualizado!',
                        icon: 'success',
                        toast: true,
                        position: 'top-end',
                        showConfirmButton: false,
                        timer: 3000
                    });
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                this.checked = !estado;  // Revertir el cambio
                Swal.fire('Error', error.message, 'error');
            }
        });
    });
}); 