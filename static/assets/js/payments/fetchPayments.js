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

    const userRole = document.body.getAttribute("data-user-role");

    if (!['Admin', 'S'].includes(userRole)){
        checkbox.disabled = true;
    }

    const month = checkbox.value;

    // Determinar si es 'pay' o 'discount'
    let type = '';
    if (checkbox.id.includes('paySwitch')) {
        type = 'pay';
    } else if (checkbox.id.includes('discountSwitch')) {
        type = 'discount';
    }

    const dataToSend = {
        obamacare: obamacare_id,  // Asegúrate de que esta variable esté definida globalmente
        month: month,
        type: type  // Solo un campo
    };

    //console.log("Enviando:", dataToSend);

    const method = checkbox.checked ? 'POST' : 'DELETE';

    fetch(`/fetchPaymentsMonth/`, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(dataToSend)
    })
    .then(response => response.json())
    .then(data => {
        //console.log("Datos recibidos:", data);
        if (data.success) {
            //console.log(checkbox.checked ? "Pago creado" : "Pago eliminado");
        } else {
            //console.error("Error:", data.message || data.errors);
        }
    })
    .catch(error => {
        //console.error('Error al procesar la respuesta:', error);
    });
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