document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.getElementById("addSubscription");
    const container = document.getElementById("subscription-container");

    addButton.addEventListener("click", function () {
        const firstItem = document.querySelector(".subscription-item");
        if (!firstItem) return;

        const newItem = firstItem.cloneNode(true);

        // Limpiar valores de los nuevos inputs
        newItem.querySelectorAll("select").forEach(select => {
            select.value = "";
        });

        // Agregar botón de remover al nuevo item
        newItem.querySelector(".remove-subscription").addEventListener("click", function () {
            newItem.remove();
        });

        container.appendChild(newItem);
    });

    // Hacer que los botones de remover funcionen en los elementos iniciales
    document.querySelectorAll(".remove-subscription").forEach(button => {
        button.addEventListener("click", function () {
            if (document.querySelectorAll(".subscription-item").length > 1) {
                button.closest(".subscription-item").remove();
            }
        });
    });
});
