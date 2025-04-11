document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.getElementById("addDependents");
    const container = document.getElementById("dependents-container");
    const submitButton = document.querySelector('button[type="submit"]');
    const form = submitButton.closest("form"); // Obtenemos el formulario padre

    submitButton.disabled = true;

    function updateSubmitState() {
        const dependentsItems = document.querySelectorAll(".dependents-item");

        const allFieldsFilled = Array.from(dependentsItems).every(item => {
            const inputs = item.querySelectorAll("input, select");
            return Array.from(inputs).every(field => {
                return field.value.trim() !== "";
            });
        });

        submitButton.disabled = !(allFieldsFilled);

    }

    addButton.addEventListener("click", function () {
        const items = container.querySelectorAll(".dependents-item");
        if (items.length >= 6) {
            alert("Solo puedes agregar hasta 6 números.");
            return;
        }

        const firstItem = items[0];
        if (!firstItem) return;

        const newItem = firstItem.cloneNode(true);

        // Limpiar valores
        newItem.querySelectorAll("input").forEach(input => {
            input.value = "";
        });

        // Botón de remover
        const removeButton = newItem.querySelector(".remove-dependents");
        if (removeButton) {
            removeButton.addEventListener("click", function () {
                newItem.remove();
                updateSubmitState();
            });
        }

        container.appendChild(newItem);
        updateSubmitState();
    });

    container.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-dependents")) {
            const items = container.querySelectorAll(".dependents-item");
            if (items.length > 1) {
                event.target.closest(".dependents-item").remove();
                updateSubmitState();
            }
        }
    });

    // Escuchar cambios en los inputs y selects del contenedor de dependientes
    document.getElementById("dependents-container").addEventListener("input", updateSubmitState);
    document.getElementById("dependents-container").addEventListener("change", updateSubmitState);

    // Validación al enviar el formulario
 

    updateSubmitState(); // Validar al cargar
});

