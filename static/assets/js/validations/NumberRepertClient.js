document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('sendClient').addEventListener('click', function(event) {
        event.preventDefault(); 
        
        const phoneNumber = document.getElementById('phone_number').value;
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
        fetch('/validatePhone/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ phone_number: phoneNumber })
        })
        .then(response => response.json())
        .then(data => {
            if (data.exists) {
                Swal.fire({
                    title: 'Este número ya existe',
                    text: 'Por favor, ingresa la clave de acceso para continuar',
                    input: 'password',
                    inputPlaceholder: 'Clave secreta',
                    showCancelButton: true,
                    confirmButtonText: 'Validar',
                    cancelButtonText: 'Cancelar',
                    inputAttributes: {
                        maxlength: 20,
                        autocapitalize: 'off',
                        autocorrect: 'off'
                    }
                }).then((result) => {
                    if (result.isConfirmed) {
                        const clave = result.value;
                        if (clave) {
                            fetch('/validateKey/', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json',
                                    'X-CSRFToken': csrfToken
                                },
                                body: JSON.stringify({
                                    access_key: clave,
                                    phone_number: phoneNumber
                                })
                            })
                            .then(response => response.json())
                            .then(data => {
                                if (data.allowed) {
                                    document.getElementById('formCreateClient').submit();
                                } else {
                                    Swal.fire({
                                        icon: 'error',
                                        title: 'Clave incorrecta',
                                        text: 'La clave ingresada no es válida.',
                                        confirmButtonColor: '#3085d6'
                                    });
                                }
                            });
                        }
                    }
                });
            } else {
                document.getElementById('formCreateClient').submit();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            Swal.fire({
                icon: 'error',
                title: 'Error inesperado',
                text: 'Ocurrió un error al validar el número de teléfono.',
                confirmButtonColor: '#3085d6'
            });
        });
    });
});


