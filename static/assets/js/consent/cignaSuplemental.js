document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('drawingCanvas');
    const ctx = canvas ? canvas.getContext('2d') : null;
    const form = document.getElementById('signatureForm');
    const signatureInput = document.getElementById('signatureInput');
    const clearCanvasButton = document.getElementById('clearCanvas');

    // ==========================
    // 🔹 Lógica de la firma (Canvas)
    // ==========================
    if (canvas && ctx) {
        let drawing = false;

        ctx.lineWidth = 5;
        ctx.lineCap = 'round';
        ctx.strokeStyle = '#000';

        const startDrawing = (event) => {
            drawing = true;
            ctx.beginPath();
            ctx.moveTo(getX(event), getY(event));
        };

        const draw = (event) => {
            if (!drawing) return;
            ctx.lineTo(getX(event), getY(event));
            ctx.stroke();
        };

        const stopDrawing = () => {
            drawing = false;
            ctx.closePath();
        };

        const getX = (event) => {
            const rect = canvas.getBoundingClientRect();
            return event.touches ? event.touches[0].clientX - rect.left : event.clientX - rect.left;
        };

        const getY = (event) => {
            const rect = canvas.getBoundingClientRect();
            return event.touches ? event.touches[0].clientY - rect.top : event.clientY - rect.top;
        };

        const isCanvasEmpty = () => {
            const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            for (let i = 0; i < pixels.length; i += 4) {
                if (pixels[i + 3] !== 0) return false;
            }
            return true;
        };

        // Eventos de dibujo
        canvas.addEventListener('mousedown', startDrawing);
        canvas.addEventListener('mousemove', draw);
        canvas.addEventListener('mouseup', stopDrawing);
        canvas.addEventListener('mouseout', stopDrawing);
        canvas.addEventListener('touchstart', startDrawing);
        canvas.addEventListener('touchmove', draw);
        canvas.addEventListener('touchend', stopDrawing);
        canvas.addEventListener('touchcancel', stopDrawing);

        // Botón limpiar
        if (clearCanvasButton) {
            clearCanvasButton.addEventListener('click', () => {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                if (signatureInput) signatureInput.value = "";
            });
        }

        // Validar antes de enviar
        if (form) {
            form.addEventListener('submit', (event) => {
                event.preventDefault();
                if (isCanvasEmpty()) {
                    canvas.focus();
                    alert('Por favor, firma antes de enviar el formulario.');
                    return;
                }
                const canvasData = canvas.toDataURL('image/png');
                if (signatureInput) signatureInput.value = canvasData;
                form.submit();
            });
        }
    }

    // ==========================
    // 🔹 Toggle de campos
    // ==========================
    function toggleFields() {
        const fields = document.querySelectorAll("#signatureForm .mb-3");
        fields.forEach(field => {
            if (field.hasAttribute("hidden")) {
                field.removeAttribute("hidden");
            } else {
                field.setAttribute("hidden", "true");
            }
        });
    }

    function focusFirstVisibleInput() {
        setTimeout(() => {
            const visibleInputs = document.querySelectorAll("#signatureForm .mb-3:not([hidden]) input, #signatureForm .mb-3:not([hidden]) textarea, #signatureForm .mb-3:not([hidden]) select");
            if (visibleInputs.length > 0) {
                visibleInputs[0].focus();
            }
        }, 200);
    }

    // ==========================
    // 🔹 Guardar borrador automático
    // ==========================
    if (form) {

        function saveDraft() {
            const formData = new FormData(form);
            const data = {};

            form.querySelectorAll("input[type=checkbox]").forEach(cb => {
                data[cb.name] = cb.checked; // true/false en lugar de "on"
            });

            formData.forEach((value, key) => {
                if (data[key] === undefined) { // si no era checkbox, meterlo normal
                    if (data[key]) {
                        if (!Array.isArray(data[key])) {
                            data[key] = [data[key]];
                        }
                        data[key].push(value);
                    } else {
                        data[key] = value;
                    }
                }
            });

            fetch(`/saveCignaDraft/${form.dataset.suppId}/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            }).catch(err => console.error("Error saving draft:", err));
        }

   

        form.querySelectorAll("input, select, textarea").forEach(el => {
            el.addEventListener("change", saveDraft);
            el.addEventListener("input", saveDraft);
        });
    }
});
