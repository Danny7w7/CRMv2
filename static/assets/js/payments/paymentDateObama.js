document.addEventListener("DOMContentLoaded", function () {
    // Inicializar flatpickr con formato m/d/Y
    flatpickr("#paymentDate", {
        dateFormat: "m/d/Y",
        allowInput: true
    });

    // Escuchar el evento de submit del formulario
    document.getElementById("paymentDateObama").addEventListener("submit", async function (event) {
        event.preventDefault();

        let form = event.target;
        let formData = new FormData(form);
        let csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
        let actionUrl = form.getAttribute("action"); // 📌 Obtiene la URL con obamacare.id y way

        // 📌 Obtener la fecha ingresada en el input
        let paymentDate = form.querySelector("#paymentDate").value.trim();

        // Verificar si la fecha tiene el formato MM/DD/YYYY
        const dateRegex = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/;
        const match = paymentDate.match(dateRegex);
  

        if (match) {
            // Extraer y reorganizar la fecha a formato YYYY-MM-DD
            let month = match[1].padStart(2, '0');  // Asegurar que el mes tenga 2 dígitos
            let day = match[2].padStart(2, '0');  // Asegurar que el día tenga 2 dígitos
            let year = match[3];
            let formattedDate = `${year}-${month}-${day}`;  // Formato final YYYY-MM-DD

            // Actualizar el valor en el FormData
            formData.set("paymentDate", formattedDate);
        } else {
            // Si la fecha no es válida, mostrar alerta y detener el envío
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
