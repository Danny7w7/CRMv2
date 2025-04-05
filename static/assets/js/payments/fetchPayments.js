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


function listenAllCheckInput() {
    let paymentsTable = document.getElementById('paymentsTable');
    let checkboxes = paymentsTable.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function(event) {
            toggleUserStatus(checkbox);
        });
    });
}

function toggleUserStatus(checkbox) {
    const formData = new FormData();
    const month = checkbox.value;  // Obtener el mes de la checkbox

    // Añadir tanto el tipo de pago como el tipo de descuento
    if (checkbox.id.includes('paySwitch')) {  // Si es el checkbox de "pago"
        formData.append('type_pay_' + month, checkbox.checked ? 'pay' : '');
    } else if (checkbox.id.includes('discountSwitch')) {  // Si es el checkbox de "descuento"
        formData.append('type_discount_' + month, checkbox.checked ? 'discount' : '');
    }

    // Asegurarse de que el mes y el valor del checkbox están siendo enviados correctamente
    console.log("Enviando:", {
        type_pay: formData.get('type_pay_' + month),
        type_discount: formData.get('type_discount_' + month),
    });

    fetch(`/fetchPaymentsMonth/`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())  // Procesar la respuesta (si es JSON)
    .then(data => {
        if (data.success) {
            console.log("Datos enviados correctamente");
        } else {
            console.error("Error al enviar los datos:", data.message);
        }
    })
    .catch(error => console.error('Error:', error));  // Manejo de errores
}

function listenAllCheckInput() {
    let paymentsTable = document.getElementById('paymentsTable');
    let checkboxes = paymentsTable.querySelectorAll('input[type="checkbox"]');

    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function(event) {
            toggleUserStatus(checkbox);
        });
    });
}

function toggleUserStatus(checkbox) {
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

    console.log("Enviando:", dataToSend);

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
        console.log("Datos recibidos:", data);
        if (data.success) {
            console.log(checkbox.checked ? "Pago creado" : "Pago eliminado");
        } else {
            console.error("Error:", data.message || data.errors);
        }
    })
    .catch(error => {
        console.error('Error al procesar la respuesta:', error);
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