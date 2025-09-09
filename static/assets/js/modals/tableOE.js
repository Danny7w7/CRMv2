
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".agent-link").forEach(link => {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const agentId = this.dataset.agentId;

            // Mostrar modal
            const modal = new bootstrap.Modal(document.getElementById("agentModal"));
            modal.show();

            // Cargar datos vía AJAX
            fetch(`/tableOE/detail/${agentId}/`, {
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(res => res.json())
            .then(data => {
                const tbody = document.getElementById("agentModalBody");
                tbody.innerHTML = "";

                if (data.data.length === 0) {
                    tbody.innerHTML = `<tr><td colspan="5" class="text-center">No hay registros</td></tr>`;
                } else {
                    data.data.forEach(item => {
                        tbody.innerHTML += `
                        <tr>
                            <td>${item.created_at}</td>
                            <td>${item.question}</td>
                            <td>${item.answer}</td>
                            <td>${item.client}</td>
                        </tr>`;
                    });
                }
            })
            .catch(err => {
                console.error("Error:", err);
                document.getElementById("agentModalBody").innerHTML =
                `<tr><td colspan="5" class="text-center text-danger">Error cargando datos</td></tr>`;
            });
        });
    });
});

