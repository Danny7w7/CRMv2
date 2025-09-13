document.addEventListener('DOMContentLoaded', function() {
    // Verificación de rol de administrador usando el atributo data en body
    const userRole = document.body.getAttribute('data-user-role');
    const isAdminRole = userRole === 'A';

    if (isAdminRole) {
        const form = document.querySelector('form');
        if (form) {
            const formElements = form.querySelectorAll('input:not([type="hidden"]), select, textarea');

            // Deshabilitar todos los campos del formulario excepto los de tipo 'hidden'
            formElements.forEach(function (element) {
                if (element.id !== 'id_client') {
                    element.disabled = true;
                }
            });

            // Manejar el div y el input de 'obs_agent'
            const divObsAgent = document.getElementById('obs_agent');
            const inputObsAgent = document.querySelector('input#obs_agent');

            // Condición para habilitar y mostrar el campo (modificar según sea necesario)
            const conditionMet = true; // Ajusta esta lógica según tus necesidades

            if (conditionMet) {
                if (divObsAgent) divObsAgent.style.display = 'block';
                if (inputObsAgent) inputObsAgent.disabled = false;
            } else {
                if (divObsAgent) divObsAgent.style.display = 'none';
            }

            // Manejo de botones submit
            const submitButton = form.querySelector('button[id="enviar"]');
            const submitButton2 = form.querySelector('button[id="enviar2"]');
            if (submitButton && submitButton2) {
                submitButton.style.display = 'none';
                submitButton2.style.display = 'inline';
            }
        }
    }

    // Configuración de Choices para select
    const selectElement = document.querySelector('#observaciones');
    if (selectElement && typeof Choices !== 'undefined') {
        new Choices(selectElement, {
            removeItemButton: true,
            searchEnabled: true,
            placeholderValue: 'Seleccione una opción...',
            itemSelectText: '',
        });
    }

    // Configuración de Flatpickr para campos de fecha
    if (typeof flatpickr !== 'undefined') {
        const datepickerConfigs = [
            "#date_birth",
            "#effectiveDateSupp", 
            "[id^='dateBirthDependent']", 
            "#date_effective_coverage", 
            "#date_effective_coverage_end",
            '#newDate',
            "paymentDate",
        ];

        datepickerConfigs.forEach(selector => {
            flatpickr(selector, { dateFormat: "m/d/Y" });
        });

        // Obtén el elemento del modal (reemplaza 'tuModalId' con el ID real de tu modal)
        const paymentModal = document.getElementById('modalPaymentsDate');

        if (paymentModal) {
            paymentModal.addEventListener('shown.bs.modal', function () {
                const paymentDateInput = document.getElementById('paymentDate');
                if (paymentDateInput) {
                    flatpickr(paymentDateInput, { dateFormat: "m/d/Y" });
                }
            });
        }
    }
});