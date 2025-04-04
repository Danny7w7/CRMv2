document.addEventListener('DOMContentLoaded', function () {
    // Obtener el rol de usuario desde el atributo del <body>
    const userRole = document.body.getAttribute('data-user-role');

    // Verifica si el usuario es del rol 'A'
    if (userRole === 'A') {
        let form = document.querySelector('form');
        if (form) {
            let formElements = form.querySelectorAll('input:not([type="hidden"]), select, textarea');
            formElements.forEach(element => {
                if (element.id !== 'id_client') {
                    element.disabled = true;
                }
            });

            // Manejo del campo obs_agent
            let divObsAgent = document.getElementById('obs_agent');
            let inputObsAgent = document.querySelector('input#obs_agent');

            let conditionMet = true; // Aquí pon la lógica real de validación
            if (conditionMet) {
                if (divObsAgent) divObsAgent.style.display = 'block';
                if (inputObsAgent) inputObsAgent.disabled = false;
            } else {
                if (divObsAgent) divObsAgent.style.display = 'none';
            }

            // Ocultar o mostrar botones submit
            let submitButton = document.querySelector('button[id="enviar"]');
            let submitButton2 = document.querySelector('button[id="enviar2"]');
            if (submitButton && submitButton2) {
                submitButton.style.display = 'none';
                submitButton2.style.display = 'inline';
            }
        }
    }

    // ⚡ Mostrar alerta si faltan datos
    let limit = parseInt(document.body.getAttribute('data-limit')) || 0;
    if (limit < 6) {
        Swal.fire({
            title: "Action required.",
            width: 500,
            padding: "2em",
            icon: "error",
            html: document.getElementById('missingDocuments')?.innerHTML || '',
            confirmButtonColor: "#3085d6",
            confirmButtonText: "OK",
            background: "#fff url(https://sweetalert2.github.io/images/trees.png)",
            backdrop: `rgba(255,0,0,0.28)`,
            didRender: () => {
                const title = Swal.getTitle();
                if (title) {
                  title.style.color = '#CC0000'; 
                  title.style.fontSize = '1.5em';
                }
              }
        });
    }

    // ⚡ Inicializar Choices.js para los select
    const selectElement = document.querySelector('#textoIngresados');
    if (selectElement) {
        new Choices(selectElement, {
            removeItemButton: true,
            searchEnabled: true,
            placeholderValue: 'Seleccione una opción...',
            itemSelectText: '',
        });
    }

    // ⚡ Inicializar Flatpickr para fechas
    flatpickr("#date_birth", { dateFormat: "m/d/Y" });
    flatpickr("[id^='dateBirthDependent']", { dateFormat: "m/d/Y" });
    flatpickr("#date_bearing", { dateFormat: "m/d/Y" });
    flatpickr("#date_effective_coverage", { dateFormat: "m/d/Y" });
    flatpickr("#date_effective_coverage_end", { dateFormat: "m/d/Y" });
    flatpickr("#dateAppointment", { dateFormat: "m/d/Y" });

    // ⚡ Validación de fecha antes de enviar formulario
    let saveAppointmentForm = document.getElementById('saveAppointment');
    if (saveAppointmentForm) {
        saveAppointmentForm.addEventListener('submit', function (event) {
            const dateInput = document.getElementById('dateAppointment');
            if (!dateInput.value) {
                event.preventDefault();
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: 'Por favor, selecciona una fecha.',
                });
            }
        });
    }
});
