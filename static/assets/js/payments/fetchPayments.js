document.addEventListener('DOMContentLoaded', function() {
    const formPaymentsOneil = document.getElementById('formPaymentsOneil');
    const formPaymentsCarrier = document.getElementById('formPaymentsCarrier');
    const formPaymentsSherpa = document.getElementById('formPaymentsSherpa');

    const formStatus = document.getElementById('formStatus');

    if (formPaymentsOneil) {
        formPaymentsOneil.addEventListener('submit', function(event) {
            fetchPayments(event, 'Oneil');
        });
    }
    if (formPaymentsCarrier){
        formPaymentsCarrier.addEventListener('submit', function(event) {
            fetchPayments(event, 'Carrier');
        });
    }
    if (formPaymentsSherpa){
        formPaymentsSherpa.addEventListener('submit', function(event) {
            fetchPayments(event, 'Sherpa');
        });
    }
    
    
    if (formStatus){
        formStatus.addEventListener('submit', function(event) {
            fetchPaymentsSuplementals(event, 'status');
        });
    }
});

function fetchPayments(event, type) {
    event.preventDefault();

    const formData = new FormData(event.target);
    
    fetch(`/fetchPayment${type}/${obamacare_id}/`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server error ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        Swal.fire({
            title: data.success ? 'Successfully' : 'Error',
            text: data.message,
            icon: data.success ? 'success' : 'error',
            showConfirmButton: true,
        }).then(() => {
            // Cerrar el modal de Bootstrap
            const modal = bootstrap.Modal.getInstance(document.getElementById(`modalChildEnterPayments${type}`));
            if (modal && data.success ) {
                modal.hide();
            }
        });
    })
    .catch((error) => {
        console.error('Error:', error);
        
    });
    
}

function fetchPaymentsSuplementals(event, type) {
    event.preventDefault();

    const formData = new FormData(event.target);
    
    fetch(`/fetchPaymentSuplementals${type}/${supp_id}/`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server error ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        Swal.fire({
            title: data.success ? 'Successfully' : 'Error',
            text: data.message,
            icon: data.success ? 'success' : 'error',
            showConfirmButton: true,
        }).then(() => {
            // Cerrar el modal de Bootstrap
            const modal = bootstrap.Modal.getInstance(document.getElementById(`modalChildEnterPayments${type}`));
            if (modal && data.success ) {
                modal.hide();
            }
        });
    })
    .catch((error) => {
        console.error('Error:', error);
        
    });
    
}