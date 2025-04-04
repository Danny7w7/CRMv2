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
    const month = checkbox.value;  // Obtener el mes de la checkbox
    const dataToSend = {
        obamacare: obamacare_id,  // Asegúrate de que `obamacare_id` está definido
        month: month,
        type_pay: checkbox.id.includes('paySwitch') && checkbox.checked ? 'pay' : '', // Si es un pago
        type_discount: checkbox.id.includes('discountSwitch') && checkbox.checked ? 'discount' : '' // Si es un descuento
    };

    console.log("Enviando:", dataToSend);

    // Si el checkbox está marcado, se hace un POST para crear el pago
    if (checkbox.checked) {
        fetch(`/fetchPaymentsMonth/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'  // Asegurarse de que el backend entienda JSON
            },
            body: JSON.stringify(dataToSend)  // Convertimos los datos a JSON
        })
        .then(response => response.json())  // Procesar la respuesta (si es JSON)
        .then(data => {
            console.log("Datos recibidos:", data);  // Ver los datos que el servidor devuelve
            if (data.success) {
                console.log("Pago creado correctamente");
            } else {
                console.error("Error al enviar los datos:", data.message);
            }
        })
        .catch(error => {
            console.error('Error al procesar la respuesta:', error);  // Mostrar error al procesar la respuesta
        });
    } 
    // Si el checkbox está desmarcado, se hace un DELETE para eliminar el pago
    else {
        fetch(`/fetchPaymentsMonth/`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'  // Asegurarse de que el backend entienda JSON
            },
            body: JSON.stringify(dataToSend)  // Convertimos los datos a JSON
        })
        .then(response => response.json())  // Procesar la respuesta (si es JSON)
        .then(data => {
            console.log("Datos recibidos:", data);  // Ver los datos que el servidor devuelve
            if (data.success) {
                console.log("Pago eliminado correctamente");
            } else {
                console.error("Error al eliminar el pago:", data.message);
            }
        })
        .catch(error => {
            console.error('Error al procesar la respuesta:', error);  // Mostrar error al procesar la respuesta
        });
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