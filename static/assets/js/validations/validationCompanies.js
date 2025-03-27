
document.addEventListener('DOMContentLoaded', function() {

    $('#tableUser').DataTable();

    // Mostrar alerta si hay mensajes en el DOM
    const alertData = document.getElementById('alert-data');
    if (alertData) {
        const type = alertData.getAttribute('data-type');
        const message = alertData.getAttribute('data-message');

        if (type === 'error') {
            Swal.fire({
                icon: "error",
                title: "Oops...",
                text: message,
            });
        } else if (type === 'good') {
            Swal.fire({
                title: "Good job!",
                text: "Company successfully saved!",
                icon: "success"
            });
        } else if (type) {
            Swal.fire({
                title: "Notification",
                text: message,
                icon: "info"
            });
        }
    }

    // Capturar el formulario
    const form = document.getElementById('formCreateCompanies');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevenir el envío del formulario
            let isValid = true;

            // Validación de número de teléfono
            const phoneNumber = document.getElementById('phone');
            if (phoneNumber) {
                let phoneNumberFormat = validatePhoneNumber(phoneNumber.value);
                if (!phoneNumberFormat) {
                    phoneNumber.focus();
                    phoneNumber.classList.add('is-invalid');
                    isValid = false;
                } else {
                    phoneNumber.value = phoneNumberFormat;
                    phoneNumber.classList.remove('is-invalid');
                }
            }

            if (isValid) {
                this.submit();
            }
        });
    }
});

// Función para validar el número de teléfono
function validatePhoneNumber(phoneNumber) {
    const cleanNumber = phoneNumber.toString().replace(/\D/g, ''); // Eliminar caracteres no numéricos
    
    if (cleanNumber.startsWith('1') && cleanNumber.length === 11) {
        return cleanNumber;
    }
    
    if (cleanNumber.length === 10) {
        return '1' + cleanNumber;
    }
    
    return false; // Número inválido
}
