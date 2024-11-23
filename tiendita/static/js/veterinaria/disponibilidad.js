let calendar;

document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando calendario...');
    initCalendar();
    initEventListeners();
});

function initCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) {
        console.error('Elemento calendario no encontrado');
        return;
    }

    try {
        calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'es',
            headerToolbar: {
                left: 'prev',
                center: 'title',
                right: 'next'
            },
            height: 650,
            selectable: true,
            selectConstraint: {
                start: new Date(),
                end: '2100-01-01'
            },
            validRange: {
                start: new Date()
            },
            events: '/api/disponibilidad/eventos/',
            dateClick: function(info) {
                const clickedDate = new Date(info.dateStr);
                const today = new Date();
                today.setHours(0, 0, 0, 0);

                if (clickedDate >= today) {
                    document.getElementById('fecha').value = info.dateStr;
                    cargarHorariosDelDia(info.dateStr);
                }
            }
        });
        
        calendar.render();
        console.log('Calendario inicializado correctamente');
    } catch (error) {
        console.error('Error al inicializar calendario:', error);
    }
}

function initEventListeners() {
    const form = document.getElementById('disponibilidadForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const horaInicio = form.querySelector('[name="hora_inicio"]').value;
            const horaFin = form.querySelector('[name="hora_fin"]').value;
            
            try {
                validarHorario(horaInicio, horaFin);
                guardarHorario(form);
            } catch (error) {
                Swal.fire('Error', error.message, 'error');
            }
        });
    }

    const fechaInput = document.getElementById('fecha');
    if (fechaInput) {
        const today = new Date().toISOString().split('T')[0];
        fechaInput.min = today;
        
        fechaInput.addEventListener('change', function() {
            cargarHorariosDelDia(this.value);
        });
    }
}


// Función para validar el horario
function validarHorario(horaInicio, horaFin) {
    const fecha = document.getElementById('fecha').value;
    if (!fecha) {
        throw new Error('Debes seleccionar una fecha');
    }

    // Validar que la fecha no sea anterior a hoy
    const fechaSeleccionada = new Date(fecha + 'T00:00:00');
    const hoy = new Date();
    
    // Establecer ambas fechas al inicio del día
    fechaSeleccionada.setHours(0, 0, 0, 0);
    hoy.setHours(0, 0, 0, 0);

    if (fechaSeleccionada.getTime() < hoy.getTime()) {
        throw new Error('No puedes agregar horarios en fechas pasadas');
    }

    // Si es hoy, validar que la hora de inicio sea posterior a la hora actual
    if (fechaSeleccionada.getTime() === hoy.getTime()) {
        const horaActual = new Date();
        const [horas, minutos] = horaInicio.split(':');
        const horaInicioDate = new Date();
        horaInicioDate.setHours(parseInt(horas), parseInt(minutos), 0, 0);
        
        if (horaInicioDate < horaActual) {
            throw new Error('La hora de inicio debe ser posterior a la hora actual');
        }
    }

    // Validar duración del horario
    const inicio = new Date(`2000-01-01T${horaInicio}`);
    const fin = new Date(`2000-01-01T${horaFin}`);
    const diferencia = (fin - inicio) / (1000 * 60);
    
    if (diferencia < 60) {
        throw new Error('El horario debe tener como mínimo una hora de duración');
    }
    
    if (diferencia > 720) {
        throw new Error('El horario no puede exceder las 12 horas');
    }
    
    return true;
}

// Función para guardar horario (actualizada)
function guardarHorario(form) {
    const formData = new FormData(form);
    
    fetch('/api/disponibilidad/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            fecha: formData.get('fecha'),
            horario_inicio: formData.get('hora_inicio'),
            horario_fin: formData.get('hora_fin')
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire('¡Éxito!', 'Horario guardado correctamente', 'success');
            cargarHorariosDelDia(formData.get('fecha'));
            if (calendar) calendar.refetchEvents();
            form.reset();
        } else {
            // Mostrar el mensaje de error limpio
            Swal.fire('Error', data.error, 'error');
        }
    })
    .catch(error => {
        Swal.fire('Error', 'Error al guardar el horario', 'error');
    });
}

// Función para cargar horarios del día
function cargarHorariosDelDia(fecha) {
    const contenedor = document.getElementById('horariosDisponibles');
    if (!contenedor) return;

    contenedor.innerHTML = '<div class="text-center py-4"><div class="spinner-border text-primary"></div></div>';

    fetch(`/api/disponibilidad/?fecha=${fecha}`)
        .then(response => response.json())
        .then(horarios => {
            if (horarios.length === 0) {
                contenedor.innerHTML = `
                    <div class="alert alert-info text-center m-3">
                        <i class="fas fa-info-circle me-2"></i>
                        No hay horarios disponibles para este día
                    </div>`;
                return;
            }

            const horariosHTML = horarios.map(horario => `
                <div class="horario-item shadow-sm">
                    <span class="horario-tiempo">
                        <i class="fas fa-clock"></i>
                        ${formatearHora(horario.HorarioInicio)} - ${formatearHora(horario.HorarioFin)}
                    </span>
                    <div class="btn-group">
                        <button class="btn btn-danger btn-sm" onclick="eliminarHorario(${horario.id})">
                            <i class="fas fa-trash-alt me-1"></i>
                            Eliminar
                        </button>
                    </div>
                </div>
            `).join('');

            contenedor.innerHTML = horariosHTML;
        })
        .catch(error => {
            contenedor.innerHTML = `
                <div class="alert alert-danger text-center m-3">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    Error al cargar los horarios
                </div>`;
        });
}

// Funciones auxiliares
function formatearHora(hora) {
    return hora ? hora.slice(0, 5) : '';
}

function eliminarHorario(id) {
    if (!id) return;

    Swal.fire({
        title: '¿Eliminar horario?',
        text: 'Esta acción no se puede deshacer',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#dc3545',
        cancelButtonColor: '#6c757d',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    }).then((result) => {
        if (result.isConfirmed) {
            fetch(`/api/disponibilidad/${id}/`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire('Eliminado', 'El horario ha sido eliminado', 'success');
                    cargarHorariosDelDia(document.getElementById('fecha').value);
                    if (calendar) calendar.refetchEvents();
                } else {
                    throw new Error(data.error || 'Error al eliminar');
                }
            })
            .catch(error => {
                Swal.fire('Error', error.message, 'error');
            });
        }
    });
}

// Función para obtener los horarios de un día específico
async function obtenerHorariosDelDia(fecha) {
    try {
        const response = await fetch(`/api/disponibilidad/?fecha=${fecha}`);
        const horarios = await response.json();
        return horarios;
    } catch (error) {
        console.error('Error al obtener horarios:', error);
        return [];
    }
}

// Función para clonar al siguiente día
async function clonarAlSiguienteDia() {
    const fecha = document.getElementById('fecha').value;
    if (!fecha) {
        Swal.fire('Error', 'Primero selecciona un día en el calendario', 'warning');
        return;
    }

    try {
        const horarios = await obtenerHorariosDelDia(fecha);
        if (horarios.length === 0) {
            Swal.fire('Error', 'No hay horarios para clonar en este día', 'warning');
            return;
        }

        // Clonar cada horario del día
        for (const horario of horarios) {
            await fetch('/api/disponibilidad/clonar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    horario_id: horario.id,
                    tipo_clon: 'siguiente'
                })
            });
        }

        Swal.fire('¡Éxito!', 'Horarios clonados al siguiente día', 'success');
        calendar.refetchEvents();
    } catch (error) {
        Swal.fire('Error', error.message, 'error');
    }
}

// Función para clonar a la semana
async function clonarALaSemana() {
    const fecha = document.getElementById('fecha').value;
    if (!fecha) {
        Swal.fire('Error', 'Primero selecciona un día en el calendario', 'warning');
        return;
    }

    try {
        const horarios = await obtenerHorariosDelDia(fecha);
        if (horarios.length === 0) {
            Swal.fire('Error', 'No hay horarios para clonar en este día', 'warning');
            return;
        }

        // Clonar cada horario del día
        for (const horario of horarios) {
            await fetch('/api/disponibilidad/clonar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: JSON.stringify({
                    horario_id: horario.id,
                    tipo_clon: 'semana'
                })
            });
        }

        Swal.fire('¡Éxito!', 'Horarios clonados a la semana', 'success');
        calendar.refetchEvents();
    } catch (error) {
        Swal.fire('Error', error.message, 'error');
    }
}

// Función para mostrar modal y clonar a día específico
async function mostrarModalClonarEspecifico() {
    const fecha = document.getElementById('fecha').value;
    if (!fecha) {
        Swal.fire('Error', 'Primero selecciona un día en el calendario', 'warning');
        return;
    }

    try {
        const horarios = await obtenerHorariosDelDia(fecha);
        if (horarios.length === 0) {
            Swal.fire('Error', 'No hay horarios para clonar en este día', 'warning');
            return;
        }

        const { value: fechaDestino } = await Swal.fire({
            title: 'Clonar a día específico',
            html: `
                <input type="date" id="fechaDestino" class="form-control" 
                       min="${new Date().toISOString().split('T')[0]}">
            `,
            showCancelButton: true,
            confirmButtonText: 'Clonar',
            cancelButtonText: 'Cancelar',
            preConfirm: () => {
                const fecha = document.getElementById('fechaDestino').value;
                if (!fecha) {
                    Swal.showValidationMessage('Selecciona una fecha destino');
                    return false;
                }
                return fecha;
            }
        });

        if (fechaDestino) {
            // Clonar cada horario del día
            for (const horario of horarios) {
                await fetch('/api/disponibilidad/clonar/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    },
                    body: JSON.stringify({
                        horario_id: horario.id,
                        tipo_clon: 'especifico',
                        fecha_destino: fechaDestino
                    })
                });
            }

            Swal.fire('¡Éxito!', 'Horarios clonados correctamente', 'success');
            calendar.refetchEvents();
        }
    } catch (error) {
        Swal.fire('Error', error.message, 'error');
    }
}

// Función para eliminar todos los horarios
async function eliminarTodosLosHorarios() {
    const fecha = document.getElementById('fecha').value;
    if (!fecha) {
        Swal.fire('Error', 'Primero selecciona un día en el calendario', 'warning');
        return;
    }

    try {
        const horarios = await obtenerHorariosDelDia(fecha);
        if (horarios.length === 0) {
            Swal.fire('Info', 'No hay horarios para eliminar en este día', 'info');
            return;
        }

        const result = await Swal.fire({
            title: '¿Eliminar todos los horarios?',
            text: `Se eliminarán ${horarios.length} horarios del día ${fecha}. Esta acción no se puede deshacer.`,
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'Sí, eliminar todos',
            cancelButtonText: 'Cancelar'
        });

        if (result.isConfirmed) {
            for (const horario of horarios) {
                await fetch(`/api/disponibilidad/${horario.id}/`, {
                    method: 'DELETE',
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });
            }

            Swal.fire('Eliminados', 'Todos los horarios han sido eliminados', 'success');
            cargarHorariosDelDia(fecha);
            if (calendar) calendar.refetchEvents();
        }
    } catch (error) {
        Swal.fire('Error', 'Error al eliminar los horarios', 'error');
    }
}