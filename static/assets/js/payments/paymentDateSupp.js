document.addEventListener("DOMContentLoaded", function () {
    // Inicializar flatpickr con formato m/d/Y
    flatpickr("#paymentDate", {
        dateFormat: "m/d/Y",
        allowInput: true
    });

    // Escuchar el evento de submit del formulario
    document.getElementById("paymentDateSupp").addEventListener("submit", async function (event) {
        event.preventDefault();

        let form = event.target;
        let formData = new FormData(form);
        let csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
        let actionUrl = form.getAttribute("action"); // 📌 Obtiene la URL con obamacare.id y way

        // 📌 Obtener y formatear la fecha antes de enviarla
        let paymentDate = form.querySelector("#paymentDate").value;

        // Verificar si la fecha tiene el formato m/d/y
        const dateRegex = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;  // Expresión regular para m/d/y
        const match = paymentDate.match(dateRegex);

        if (match) {
            // Reorganizar la fecha a formato YYYY-MM-DD
            const month = match[1].padStart(2, '0');  // Asegura que el mes tenga 2 dígitos
            const day = match[2].padStart(2, '0');  // Asegura que el día tenga 2 dígitos
            const year = match[3];
            paymentDate = `${year}-${month}-${day}`;  // Formato final YYYY-MM-DD

            // Verificar el formato de la fecha antes de enviarla
            console.log("Formatted Date:", paymentDate);

            // Actualizar el valor de paymentDate en el FormData
            formData.set("paymentDate", paymentDate);
        } else {
            // Si el formato no es válido, prevenir el envío del formulario y mostrar alerta
            Swal.fire({
                icon: 'error',
                title: 'Invalid Date Format',
                text: 'Please enter the date in the format MM/DD/YYYY.',
            });
            return;
        }

        try {
            let response = await fetch(actionUrl, {
                method: "POST",
                body: formData,
                headers: {
                    "X-CSRFToken": csrfToken
                }
            });

            let data = await response.json();

            if (response.ok) {
                Swal.fire({
                    title: "Success!",
                    text: data.message,
                    icon: "success",
                    confirmButtonText: "OK",
                    timer: 2000
                }).then(() => {
                    let modal = bootstrap.Modal.getInstance(document.getElementById("modalPaymentsDate"));
                    modal.hide();
                });
            } else {
                Swal.fire({
                    title: "Error!",
                    text: data.error || "Error saving appointment",
                    icon: "error",
                    confirmButtonText: "Try Again"
                });
            }
        } catch (error) {
            Swal.fire({
                title: "Server Error!",
                text: "An unexpected error occurred",
                icon: "error",
                confirmButtonText: "OK"
            });
        }
    });
});
