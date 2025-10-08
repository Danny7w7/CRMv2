
document.addEventListener('DOMContentLoaded', function() {
    let recordId = null;
    let recordType = null;
    let redirectUrl = null;

    const modal = document.getElementById('monitoringModal');
    const contentInput = document.getElementById('monitoringContent');
    const saveBtn = document.getElementById('saveMonitoringBtn');

    if (!modal || !saveBtn || !contentInput) return;

    // Cuando se abre el modal
    modal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        recordId = button.getAttribute('data-id');
        recordType = button.getAttribute('data-type');
        redirectUrl = button.getAttribute('data-url');

        // 🧹 Limpia el campo de texto al abrir
        contentInput.value = '';
    });

    // Guardar y redirigir
    saveBtn.addEventListener('click', function() {
        const content = contentInput.value.trim();
        if (!content) {
            alert("Por favor, escribe una nota antes de continuar.");
            return;
        }

        fetch(saveMonitoringURL, {
            method: "POST",
            headers: {
                "X-CSRFToken": CSRF_TOKEN,
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                record_id: recordId,
                record_type: recordType,
                content: content
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                window.location.href = redirectUrl;
            } else {
                alert("Error al guardar el seguimiento: " + (data.error || ""));
            }
        })
        .catch(err => {
            console.error(err);
            alert("Error al enviar la solicitud.");
        });
    });
});

