document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.getElementById("addNumbers");
    const container = document.getElementById("numbers-container");

    addButton.addEventListener("click", function () {
        const firstItem = document.querySelector(".numbers-item");
        if (!firstItem) return;

        const newItem = firstItem.cloneNode(true);

        // Limpiar valores de los nuevos inputs
        newItem.querySelectorAll("input").forEach(input => {
            input.value = "";
        });

        // Agregar botón de remover al nuevo item
        const removeButton = newItem.querySelector(".remove-numbers");
        if (removeButton) {
            removeButton.addEventListener("click", function () {
                newItem.remove();
            });
        }

        container.appendChild(newItem);
    });

    // Hacer que los botones de remover funcionen en los elementos iniciales
    container.addEventListener("click", function (event) {
        if (event.target.classList.contains("remove-numbers")) {
            if (document.querySelectorAll(".numbers-item").length > 1) {
                event.target.closest(".numbers-item").remove();
            }
        }
    });
});