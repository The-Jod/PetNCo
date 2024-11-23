let calendar = null;

function initCalendar() {
    const calendarEl = document.getElementById('calendar');
    if (!calendarEl) return;

    // Obtener la fecha actual sin hora
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        locale: 'es',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: ''
        },
        height: 'auto',
        handleWindowResize: true,
        dayMaxEvents: true,
        events: '/api/disponibilidad/eventos/',
        dateClick: function(info) {
            // Convertir la fecha clickeada a fecha local
            const clickedDate = new Date(info.dateStr + 'T00:00:00');
            const today = new Date();
            
            // Normalizar ambas fechas a medianoche
            clickedDate.setHours(0, 0, 0, 0);
            today.setHours(0, 0, 0, 0);

            // Convertir a timestamps para comparación
            const clickedTimestamp = clickedDate.getTime();
            const todayTimestamp = today.getTime();
            
            // Permitir el día actual y futuros, bloquear días pasados
            if (clickedTimestamp >= todayTimestamp) {
                document.getElementById('fecha').value = info.dateStr;
                cargarHorariosDelDia(info.dateStr);
            } else {
                Swal.fire('Error', 'No puedes agregar horarios en fechas pasadas', 'error');
            }
        },
        eventDidMount: function(info) {
            info.el.classList.add('has-events');
        },
        // Deshabilitar fechas anteriores a hoy
        validRange: {
            start: today
        },
        // Cambiar el color de los días pasados
        dayCellClassNames: function(arg) {
            const date = new Date(arg.date);
            const today = new Date();
            
            date.setHours(0, 0, 0, 0);
            today.setHours(0, 0, 0, 0);
            
            if (date.getTime() < today.getTime()) {
                return ['fc-day-disabled'];
            }
            return [];
        }
    });

    calendar.render();
}

// Función para manejar el envío del formulario
async function handleFormSubmit(event) {
    event.preventDefault();
    
    try {
        const form = event.target;
        const formData = new FormData(form);
        
        // Validar teléfono
        const telefono = formData.get('telefono');
        if (!/^\d{9}$/.test(telefono)) {
            throw new Error('El número de teléfono debe tener exactamente 9 dígitos');
        }
        
        // Agregar el prefijo +56 al teléfono
        formData.set('telefono', '+56' + telefono);
        
        // Realizar la petición
        const response = await fetch('/veterinario/perfil/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Error al actualizar el perfil');
        }
        
        // Si todo salió bien
        await Swal.fire({
            title: '¡Éxito!',
            text: 'Perfil actualizado correctamente',
            icon: 'success'
        });
        
        // Cerrar el modal y recargar la página
        const modal = bootstrap.Modal.getInstance(document.getElementById('editarPerfilModal'));
        if (modal) {
            modal.hide();
        }
        window.location.reload();
        
    } catch (error) {
        console.error('Error:', error);
        await Swal.fire({
            title: 'Error',
            text: error.message || 'Hubo un error al actualizar el perfil',
            icon: 'error'
        });
    }
}

// Función para validar el teléfono en tiempo real
function validatePhone(input) {
    const value = input.value.replace(/\D/g, '');
    input.value = value.substring(0, 9);
    
    if (value.length !== 9) {
        input.setCustomValidity('El número debe tener 9 dígitos');
        input.classList.add('is-invalid');
    } else {
        input.setCustomValidity('');
        input.classList.remove('is-invalid');
    }
}

// Inicialización cuando el documento está listo
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar calendario si existe
    initCalendar();
    
    // Inicializar el formulario de edición de perfil
    const formEditarPerfil = document.getElementById('formEditarPerfil');
    if (formEditarPerfil) {
        formEditarPerfil.addEventListener('submit', function(e) {
            e.preventDefault(); // Prevenir el envío normal del formulario
            
            if (!validateForm(this)) {
                return;
            }

            const formData = new FormData(this);
            
            fetch(this.action, {  // Usar la URL del action del formulario
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'X-Requested-With': 'XMLHttpRequest'  // Indicar que es una petición AJAX
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Éxito!',
                        text: data.message || 'Perfil actualizado correctamente',
                        showConfirmButton: false,
                        timer: 1500
                    }).then(() => {
                        const modal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
                        if (modal) {
                            modal.hide();
                        }
                        window.location.reload();
                    });
                } else {
                    throw new Error(data.error || 'Error al actualizar el perfil');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: error.message || 'Error al actualizar el perfil'
                });
            });
        });
    }

    // Manejar cambio en el switch de activación
    const switchEstadoPerfil = document.getElementById('estaActivo');
    if (switchEstadoPerfil) {
        switchEstadoPerfil.addEventListener('change', function() {
            const estado = this.checked;
            const mensaje = estado ? 
                '¿Estás seguro de que quieres activar tu perfil? Aparecerás en las búsquedas de veterinarios.' :
                '¿Estás seguro de que quieres desactivar tu perfil? Ya no aparecerás en las búsquedas de veterinarios.';

            Swal.fire({
                title: '¿Estás seguro?',
                text: mensaje,
                icon: 'warning',
                showCancelButton: true,
                confirmButtonColor: '#3085d6',
                cancelButtonColor: '#d33',
                confirmButtonText: 'Sí, confirmar',
                cancelButtonText: 'Cancelar'
            }).then((result) => {
                if (!result.isConfirmed) {
                    // Si el usuario cancela, revertir el switch
                    this.checked = !estado;
                }
            });
        });
    }
});

// Función de validación
function validateForm(form) {
    const telefono = form.querySelector('[name="telefono"]').value.trim();
    if (!/^(9\d{8}|22\d{7})$/.test(telefono)) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'El número debe comenzar con 9 (celular) o 22 (fijo) seguido de 8 o 7 dígitos respectivamente'
        });
        return false;
    }

    const descripcion = form.querySelector('[name="descripcion"]').value.trim();
    if (descripcion.length < 50) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'La descripción debe tener al menos 50 caracteres'
        });
        return false;
    }

    return true;
}

// Función para actualizar el precio del servicio
async function actualizarPrecioServicio(servicioId, precio) {
    try {
        const response = await fetch('/api/servicios/personalizado/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                accion: 'actualizar_precio',
                servicio_id: servicioId,
                precio: precio
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Error al actualizar el precio');
        }

        const data = await response.json();
        if (data.success) {
            Swal.fire({
                title: '¡Actualizado!',
                text: 'Precio actualizado correctamente',
                icon: 'success',
                toast: true,
                position: 'top-end',
                showConfirmButton: false,
                timer: 3000
            });
        }
    } catch (error) {
        Swal.fire('Error', error.message, 'error');
    }
}

// Función para previsualizar la imagen antes de subirla
document.addEventListener('DOMContentLoaded', function() {
    const inputImagen = document.querySelector('input[name="imagen"]');
    if (inputImagen) {
        inputImagen.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const previewImg = document.querySelector('.profile-image');
                    if (previewImg) {
                        previewImg.src = e.target.result;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    }
});

// Función para formatear RUT (de número a formato con puntos y guión)
function formatearRut(rut) {
    rut = rut.toString();
    const dv = rut.slice(-1);
    const rutCuerpo = rut.slice(0, -1);
    let rutFormateado = rutCuerpo.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    return `${rutFormateado}-${dv}`;
}

// Función para validar RUT (simplificada)
function validarRut(rut) {
    // Limpiar el RUT de cualquier carácter que no sea número
    const rutLimpio = rut.replace(/\D/g, '');
    // Verificar que tenga al menos 7 números
    return rutLimpio.length >= 7;
}

// Función para formatear RUT mientras se escribe
function formatearRutAlEscribir(rut) {
    // Mantener solo números
    let valor = rut.replace(/\D/g, '');
    
    // Limitar la longitud máxima a 9 dígitos
    valor = valor.substring(0, 14);
    
    return valor;
}

// Evento para el input del RUT
document.addEventListener('DOMContentLoaded', function() {
    const rutInput = document.getElementById('rutInput');
    if (rutInput) {
        // Formatear el valor inicial si existe
        if (rutInput.value) {
            rutInput.value = formatearRutAlEscribir(rutInput.value);
        }

        rutInput.addEventListener('input', function(e) {
            let rutFormateado = formatearRutAlEscribir(e.target.value);
            e.target.value = rutFormateado;
            
            // Validar longitud mínima
            if (rutFormateado.length < 7) {
                e.target.setCustomValidity('El RUT debe tener al menos 7 números');
                rutInput.classList.add('is-invalid');
            } else {
                e.target.setCustomValidity('');
                rutInput.classList.remove('is-invalid');
            }
        });
    }
});

// Función para formatear visualmente el RUT (solo para mostrar)
function formatearRutVisual(rut) {
    // Limpiar el rut de cualquier carácter que no sea número
    let valor = rut.replace(/\D/g, '');
    
    // Si no hay valor, retornar vacío
    if (!valor) return '';
    
    // Obtener el cuerpo y dígito verificador
    let cuerpo = valor.slice(0, -1);
    let dv = valor.slice(-1);
    
    // Formatear el cuerpo con puntos
    let rutFormateado = '';
    while (cuerpo.length > 3) {
        rutFormateado = '.' + cuerpo.slice(-3) + rutFormateado;
        cuerpo = cuerpo.slice(0, -3);
    }
    rutFormateado = cuerpo + rutFormateado;
    
    // Agregar el guión y dígito verificador
    return rutFormateado + '-' + dv;
}

// Evento para el input del RUT
document.addEventListener('DOMContentLoaded', function() {
    const rutInput = document.getElementById('rutInput');
    if (rutInput) {
        // Formatear el valor inicial si existe
        if (rutInput.value) {
            rutInput.value = formatearRutVisual(rutInput.value);
        }

        rutInput.addEventListener('input', function(e) {
            // Obtener solo los números del input
            let numeros = e.target.value.replace(/\D/g, '');
            
            // Limitar a 9 dígitos
            numeros = numeros.substring(0, 12);
            
            // Formatear visualmente
            e.target.value = formatearRutVisual(numeros);
            
            // Validar longitud mínima (usando solo números)
            if (numeros.length < 7) {
                e.target.setCustomValidity('El RUT debe tener al menos 7 nmeros');
                rutInput.classList.add('is-invalid');
            } else {
                e.target.setCustomValidity('');
                rutInput.classList.remove('is-invalid');
            }
        });
    }
});

// Agregar esta función para validar el teléfono
function validarTelefono(telefono) {
    // Eliminar cualquier carácter no numérico
    const numeroLimpio = telefono.replace(/\D/g, '');
    return numeroLimpio.length === 9;
}

// Agregar validación al input del teléfono
document.addEventListener('DOMContentLoaded', function() {
    const telefonoInput = document.getElementById('telefonoInput');
    if (telefonoInput) {
        telefonoInput.addEventListener('input', function(e) {
            // Permitir solo números
            let valor = e.target.value.replace(/\D/g, '');
            
            // Limitar a 9 dígitos
            valor = valor.substring(0, 9);
            
            // Actualizar el valor del input
            e.target.value = valor;
            
            // Validar longitud
            if (valor.length !== 9) {
                e.target.setCustomValidity('El número debe tener 9 dígitos');
                e.target.classList.add('is-invalid');
            } else {
                e.target.setCustomValidity('');
                e.target.classList.remove('is-invalid');
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function() {
    initializeProfileImage();
    initializeProfileForm();
    initializePhoneInput();
});

function initializeProfileImage() {
    const imageInput = document.getElementById('profile-image-input');
    if (!imageInput) return;

    imageInput.addEventListener('change', async function(e) {
        const file = e.target.files[0];
        if (!file) return;

        // Validar tipo de archivo
        const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
        if (!validTypes.includes(file.type)) {
            Swal.fire('Error', 'Por favor seleccione una imagen en formato JPG, PNG o WEBP', 'error');
            return;
        }

        // Validar tamaño (máximo 5MB)
        if (file.size > 5 * 1024 * 1024) {
            Swal.fire('Error', 'La imagen no debe superar los 5MB', 'error');
            return;
        }

        try {
            const formData = new FormData();
            formData.append('imagen_perfil', file);
            formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

            const response = await fetch('/api/veterinario/actualizar-imagen/', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            if (data.success) {
                document.getElementById('current-profile-image').src = data.image_url;
                Swal.fire('¡Éxito!', 'Imagen de perfil actualizada', 'success');
            } else {
                throw new Error(data.error || 'Error al actualizar la imagen');
            }
        } catch (error) {
            Swal.fire('Error', error.message, 'error');
        }
    });
}

function initializeProfileForm() {
    const form = document.getElementById('profile-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        try {
            // Validar campos antes de enviar
            if (!validateForm(this)) {
                return;
            }

            const formData = new FormData(this);
            
            // Formatear el teléfono antes de enviar
            const telefono = formData.get('telefono');
            formData.set('telefono', '9' + telefono); // Agregar el 9 inicial

            const response = await fetch('/api/veterinario/actualizar-perfil/', {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: formData
            });

            const data = await response.json();
            if (data.success) {
                // Cerrar el modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
                modal.hide();

                Swal.fire({
                    icon: 'success',
                    title: '¡Perfil actualizado!',
                    text: 'Los cambios se han guardado correctamente.',
                    showConfirmButton: false,
                    timer: 1500
                }).then(() => {
                    window.location.reload();
                });
            } else {
                throw new Error(data.error || 'Error al actualizar el perfil');
            }
        } catch (error) {
            Swal.fire('Error', error.message, 'error');
        }
    });
}

function initializePhoneInput() {
    const phoneInput = document.querySelector('input[name="telefono"]');
    if (!phoneInput) return;

    phoneInput.addEventListener('input', function(e) {
        // Remover cualquier caracter que no sea número
        let value = this.value.replace(/\D/g, '');
        
        // Limitar a 8 dígitos (sin contar el 9 inicial)
        value = value.slice(0, 8);
        
        // Actualizar el valor del input
        this.value = value;
        
        // Validar longitud
        if (value.length === 8) {
            this.setCustomValidity('');
            this.classList.remove('is-invalid');
        } else {
            this.setCustomValidity('El número debe tener 8 dígitos después del 9');
            this.classList.add('is-invalid');
        }
    });
}

// Función auxiliar para formatear el teléfono en la vista
function formatPhoneNumber(phone) {
    const cleaned = ('' + phone).replace(/\D/g, '');
    const match = cleaned.match(/^(\d{1})(\d{4})(\d{4})$/);
    if (match) {
        return `+56 ${match[1]} ${match[2]} ${match[3]}`;
    }
    return phone;
}

// Manejo de la actualización de imagen
document.getElementById('profile-image-input').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('imagen_perfil', file);

    fetch('/api/veterinario/actualizar-imagen/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar la imagen en la página
            document.getElementById('current-profile-image').src = data.image_url;
            Swal.fire({
                icon: 'success',
                title: '¡Éxito!',
                text: data.message
            });
        } else {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Error al actualizar la imagen'
        });
    });
});

// Manejo del formulario de perfil
document.getElementById('formEditarPerfil').addEventListener('submit', function(e) {
    e.preventDefault();

    if (!validateForm(this)) {
        return;
    }

    const formData = new FormData(this);
    
    // Validar teléfono
    const telefono = formData.get('telefono');
    if (!/^\d{9}$/.test(telefono)) {
        Swal.fire('Error', 'El número de teléfono debe tener 9 dígitos', 'error');
        return;
    }

    // Enviar a la URL correcta
    fetch('/veterinario/perfil/actualizar/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || 'Error al actualizar el perfil');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: '¡Éxito!',
                text: 'Perfil actualizado correctamente',
                showConfirmButton: false,
                timer: 1500
            }).then(() => {
                // Cerrar el modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('editProfileModal'));
                if (modal) {
                    modal.hide();
                }
                window.location.reload();
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: error.message || 'Error al actualizar el perfil'
        });
    });
});

function validateForm(form) {
    // Validar teléfono
    const telefono = form.querySelector('[name="telefono"]').value.trim();
    if (!/^(9\d{8}|22\d{7})$/.test(telefono)) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'El número debe comenzar con 9 (celular) o 22 (fijo) seguido de 8 o 7 dígitos respectivamente'
        });
        return false;
    }

    // Validar descripción
    const descripcion = form.querySelector('[name="descripcion"]').value.trim();
    if (descripcion.length < 50) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'La descripción debe tener al menos 50 caracteres'
        });
        return false;
    }

    return true;
} 
}); 