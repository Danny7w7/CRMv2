document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".typeSalesForm").forEach(form => {
        form.addEventListener("submit", function(e) {
            e.preventDefault();

            let formData = new FormData(form);

            fetch(form.action, {
                method: "POST",
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === "error") {
                    Swal.fire({
                        icon: "error",
                        title: "Error",
                        text: data.message
                    });
                } else if (data.status === "success") {
                
                    window.location.href = data.redirect_url;
                
                }
            })
            .catch(error => {
                Swal.fire({
                    icon: "error",
                    title: "Error",
                    text: "Ocurrió un problema en la solicitud."
                });
            });
        });
    });
});