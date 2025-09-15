document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('#changeDateForm, #changeAgentForm');
    console.log(forms)

    forms.forEach(form => {
        form.addEventListener('submit', event => {
            event.preventDefault();
            let typeChange = 'Date';
            if (form.id.includes('Agent')) {
                typeChange = 'Agent';
            }

            const actionUrl = form.getAttribute('action');

            fetch(actionUrl, { method: 'POST', body: new FormData(form) })
            .then(response => {
                if (response.ok) {
                    Swal.fire({
                        icon: 'success',
                        title: '¡Success!',
                        text: `${typeChange} change request successfully created`,
                    })
                    showOrHideModal(`change${typeChange}`, false);
                    document.getElementById('optionsColumn').textContent = ``;
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: '¡Error!',
                        text: `${typeChange} change request failed`,
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});

function showOrHideModal(modalId, show = true) {
    const modal = document.getElementById(modalId);
    
    if (!modal) {
        console.error(`Modal with ID ${modalId} not found.`);
        return;
    }
    
    // Intenta obtener la instancia existente primero
    let bsModal = bootstrap.Modal.getInstance(modal);
    
    // Si no existe instancia, créala
    if (!bsModal) {
        bsModal = new bootstrap.Modal(modal);
    }

    if (show){
        bsModal.show();
    }else{
        bsModal.hide();
    }
}

function buttonApproveChangeDate(logId, approve, typePlan) {
    fetch(`/fetchChangePlanDate/${logId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            'approve':approve,
            'type_plan':typePlan
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json(); // o response.text() según lo que devuelva tu backend
    })
    .then(data => {
        Swal.fire({
            icon: 'success',
            title: '¡Success!',
            text: `Date Change request successfully ${approve ? 'approved' : 'rejected'}`,
        })
        .then(() => {
            document.getElementById(`optionsColumn${logId}`).textContent = `${data.status} by ${data.user} on ${new Date().toLocaleDateString()}`;
        });
    })
    .catch(err => {
        Swal.fire({
            icon: 'error',
            title: 'Error!',
            text: `Date Change request failed: ${err.message}`,
        });
    });
}

function buttonApproveChangeAgent(logId, approve, typePlan) {
    fetch(`/fetchChangePlanAgent/${logId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            'approve':approve,
            'type_plan':typePlan
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json(); // o response.text() según lo que devuelva tu backend
    })
    .then(data => {
        Swal.fire({
            icon: 'success',
            title: '¡Success!',
            text: `Agent Change request successfully ${approve ? 'approved' : 'rejected'}`,
        });
    })
    .catch(err => {
        Swal.fire({
            icon: 'error',
            title: 'Error!',
            text: `Agent Change request failed: ${err.message}`,
        });
    });
}

function showReasonChange(typeChange, reasonId) {
    fetch(`/getReasonChange/${reasonId}/?type=${typeChange}`, {
        method: 'GET',

        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(response.error || 'Error fetching reason');
        }
        return response.json(); // <- aquí conviertes la respuesta a JSON
    })
    .then(data => {
        // aquí ya puedes acceder a data.message o cualquier otra propiedad
        Swal.fire({
            icon: 'info',
            title: 'Reason',
            text: data.reason,
        });
    })
    .catch(error => {
        Swal.fire({
            icon: 'error',
            title: '¡Error!',
            text: error.message,
        });
    });
}
