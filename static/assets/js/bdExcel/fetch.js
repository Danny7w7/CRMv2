document.addEventListener('DOMContentLoaded', function() {
    // Manejar el envío de formularios de observación
    const forms = document.querySelectorAll('.form-observation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const recordId = formData.get('record_id');
            const observation = formData.get('observation');
            
            // Validación básica
            if (!observation || observation === 'no_valid') {
                Swal.fire({
                    title: 'Error',
                    text: 'Please select a valid option.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
                return;
            }
            
            // Usar la URL desde la variable global
            fetch(window.djangoUrls.saveCommentAjax, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    Swal.fire({
                        title: 'Success',
                        text: data.message,
                        icon: 'success',
                        confirmButtonText: 'OK'
                    }).then(() => {
                        // Recargar la página para mostrar los cambios
                        location.reload();
                    });
                } else {
                    Swal.fire({
                        title: 'Error',
                        text: data.message,
                        icon: 'error',
                        confirmButtonText: 'OK'
                    });
                }
            })
            .catch(error => {
                console.error('Error:', error);
                Swal.fire({
                    title: 'Error',
                    text: 'An error occurred while saving the observation.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            });
        });
    });
});