function listenAllCheckInput() {
    let paymentsTable = document.getElementById('paymentsTable');
    let checkboxes = paymentsTable.querySelectorAll('input[type="checkbox"]');

    let actionRequiredTable = document.getElementById('actionRequiredTable');
    let checkboxesActionRequired = actionRequiredTable.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function(event) {            
            toggleUserStatus(checkbox);
        });
    });

    checkboxesActionRequired.forEach(function(checkbox) {
        // Elimina el evento anterior solo si ya existe
        checkbox.removeEventListener('change', toogleActionRequired);

        checkbox.addEventListener('change', function(event) {  
            toogleActionRequired(checkbox);
        });
    });
}


function toggleUserStatus(checkbox) {
    const formData = new FormData();
    formData.append('obamaCare', obamacare_id);
    formData.append('month', checkbox.value);

    if (checkbox.checked) {

        fetch(`/fetchPaymentsMonth/`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())  // Procesar la respuesta (si es JSON)
        .then(data => {
            if (data.success){
                if (data.success && data.role != "Admin") {
                    checkbox.disabled = true;
                }
            }
        })
        .catch(error => console.error('Error:', error));  // Manejo de errores
    } else {
        // Si se desmarca el checkbox, eliminar el pago
        fetch(`/fetchPaymentsMonth/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                obamaCare: obamacare_id,
                month: checkbox.value
            })
        })
        .then(response => response.json())  
        .then(data => {
            if (data.success) {
                console.log("Payment deleted successfully");
            } else {
                console.error("Error deleting payment:", data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

// fetch para Action Required
let isRequestPending = false;

function toogleActionRequired(checkbox) {
    if (isRequestPending) return; // Evita enviar otra petición si ya hay una en curso
    isRequestPending = true;

    const checkboxId = checkbox.value;
    const formData = new FormData();
    formData.append('id', checkboxId);

    fetch('/fetchActionRequired/', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        return response.json();
    })
    .then(data => {
        checkbox.disabled = true;
    })
    .catch(error => {
        console.error('Error:', error);
    })
    .finally(() => {
        isRequestPending = false; // Habilita de nuevo las peticiones
    });
}



document.addEventListener('DOMContentLoaded', listenAllCheckInput);