// Función para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Función principal para enviar el formulario
async function submitForm() {
    const formElement = document.querySelector('form');
    const formData = new FormData(formElement);
    const csrftoken = getCookie('csrftoken');

    try {
        const response = await fetch('/formCreateFinalExpenses/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrftoken,
            }
        });

        const data = await response.json();

        if (data.status === 'success') {
            Swal.fire({
                icon: 'success',
                title: '¡Éxito!',
                text: data.message,
                confirmButtonText: 'Aceptar'
            }).then(() => {
                window.location.reload();
            });
        } else {
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: data.message || 'Ocurrió un error desconocido',
                confirmButtonText: 'Entendido'
            });
        }
    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Error de conexión',
            text: 'No se pudo contactar al servidor: ' + error.message,
            confirmButtonText: 'Entendido'
        });
    }
}

// Al cargar el DOM
document.addEventListener('DOMContentLoaded', function () {
    // Activar Flatpickr
    if (document.querySelector('#date_birth')) {
        flatpickr("#date_birth", {
            dateFormat: "m/d/Y",
        });
    }

    // Activar botón de envío
    const submitButton = document.querySelector('.btn-submit-form');
    if (submitButton) {
        submitButton.addEventListener('click', function (e) {
            e.preventDefault();
            submitForm();
        });
    }
});
