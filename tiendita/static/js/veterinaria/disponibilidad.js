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
                start: new Date().setHours(0,0,0,0),
                end: '2100-01-01'
            },
            validRange: {
                start: new Date().setHours(0,0,0,0)
            },
            events: '/api/disponibilidad/eventos/',
            dateClick: function(info) {
                const clickedDate = new Date(info.dateStr + 'T00:00:00');
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                clickedDate.setHours(0, 0, 0, 0);

                console.log('Fecha clickeada:', clickedDate);
                console.log('Hoy:', today);

                if (clickedDate >= today) {
                    document.getElementById('fecha').value = info.dateStr;
                    cargarHorariosDelDia(info.dateStr);
                    
                    const prevSelected = document.querySelector('.fc-day-selected');
                    if (prevSelected) {
                        prevSelected.classList.remove('fc-day-selected');
                    }
                    info.dayEl.classList.add('fc-day-selected');
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
    const data = {
        fecha: formData.get('fecha'),
        horario_inicio: formData.get('hora_inicio'),
        horario_fin: formData.get('hora_fin')
    };

    console.log('Enviando datos:', data); // Para debug

    fetch('/api/disponibilidad/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            Swal.fire('¡Éxito!', data.message || 'Horario guardado correctamente', 'success');
            cargarHorariosDelDia(formData.get('fecha'));
            if (calendar) calendar.refetchEvents();
            form.reset();
        } else {
            Swal.fire('Error', data.error || 'Error al guardar el horario', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire('Error', 'Error al guardar el horario', 'error');
    });
}

// Función para cargar horarios del día
function cargarHorariosDelDia(fecha) {
    if (!fecha) return;

    console.log('Cargando horarios para:', fecha);  // Debug

    fetch(`/api/disponibilidad/?fecha=${fecha}`)
        .then(response => {
            console.log('Response status:', response.status);  // Debug
            if (!response.ok) {
                throw new Error('Error al cargar horarios');
            }
            return response.json();
        })
        .then(horarios => {
            console.log('Horarios recibidos:', horarios);  // Debug
            const contenedor = document.querySelector('#horariosDisponibles');
            if (!contenedor) {
                console.error('Contenedor de horarios no encontrado');
                return;
            }

            contenedor.innerHTML = '';
            
            if (!Array.isArray(horarios) || horarios.length === 0) {
                contenedor.innerHTML = '<p class="text-muted">No hay horarios disponibles para este día</p>';
                return;
            }

            horarios.forEach(horario => {
                const elemento = document.createElement('div');
                elemento.className = 'horario-item mb-2 p-3 border rounded';
                elemento.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <span class="horario-tiempo">
                            <i class="fas fa-clock"></i>
                            ${horario.inicio} - ${horario.fin}
                        </span>
                        <button class="btn btn-danger btn-sm" onclick="eliminarHorario(${horario.id})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                `;
                contenedor.appendChild(elemento);
            });
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire('Error', 'No se pudieron cargar los horarios', 'error');
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

function actualizarListaHorarios(horarios) {
    const container = document.getElementById('horariosDisponibles');
    container.innerHTML = '';
    
    if (!horarios || horarios.length === 0) {
        container.innerHTML = '<p class="text-muted text-center py-3">No hay horarios disponibles para este día</p>';
        return;
    }
    
    horarios.forEach(horario => {
        const estado = {
            'disponible': 'success',
            'reservado': 'warning',
            'expirado': 'danger',
            'cancelado': 'secondary'
        }[horario.estado];

        container.innerHTML += `
            <div class="horario-row">
                <div class="horario-content">
                    <i class="fas fa-clock text-primary"></i>
                    <span class="horario-text">${horario.inicio} - ${horario.fin}</span>
                </div>
                <div class="horario-actions">
                    <button class="delete-button" onclick="eliminarHorario(${horario.id})">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </div>
            </div>
        `;
    });
}