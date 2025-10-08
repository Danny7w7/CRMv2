document.addEventListener('DOMContentLoaded', function () {
    const modal = new bootstrap.Modal(document.getElementById('submitModal'));
    const openModalBtn = document.getElementById('openSubmitModal');
    const confirmBtn = document.getElementById('confirmSubmitBtn');
    const noteInput = document.getElementById('noteContent');
    const form = document.querySelector('form'); // el formulario principal

    if (!openModalBtn || !form) return;

    // Abre el modal cuando se hace clic en “Submit”
    openModalBtn.addEventListener('click', function (e) {
        e.preventDefault();
        noteInput.value = ""; // limpia el campo
        modal.show();
    });

    // Cuando se confirma en el modal
    confirmBtn.addEventListener('click', function () {
        const note = noteInput.value.trim();

        if (!note) {
            alert("Please write a note before sending.");
            return;
        }

        // Creamos o actualizamos un campo oculto para enviar la nota
        let hiddenInput = form.querySelector('input[name="monitoring_note"]');
        if (!hiddenInput) {
            hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'monitoring_note';
            form.appendChild(hiddenInput);
        }

        hiddenInput.value = note;

        // Creamos o aseguramos el campo action
        let actionInput = form.querySelector('input[name="action"]');
        if (!actionInput) {
            actionInput = document.createElement('input');
            actionInput.type = 'hidden';
            actionInput.name = 'action';
            form.appendChild(actionInput);
        }

        actionInput.value = 'save_obamacare';

        // Envía el formulario
        form.submit();
    });
});
