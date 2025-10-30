document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('.form-observation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(form);
            const recordId = formData.get('record_id');
            const observation = formData.get('observation');
            
            if (!observation || observation === 'no_valid') {
                Swal.fire({
                    title: 'Error',
                    text: 'Please select a valid option.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
                return;
            }
            
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
                    });

                    // 🟢 Actualizar icono de "Sold"
                    const row = form.closest('tr');
                    const soldCell = row.querySelector('td:first-child');
                    if (soldCell) {
                        if (data.is_sold) {
                            soldCell.innerHTML = `<div class="font-35 text-success"><i class='bx bxs-check-circle'></i></div>`;
                        } else {
                            soldCell.innerHTML = `<div class="font-35 text-danger"><i class='bx bxs-message-square-x'></i></div>`;
                        }
                    }

                    // 📝 Agregar comentario al modal correspondiente
                    const modalBody = document.querySelector(`#modalVerTexto_${data.record_id} .modal-body`);
                    if (modalBody && data.comment) {
                        const newComment = document.createElement('ul');
                        newComment.classList.add('list-group');
                        newComment.innerHTML = `
                            <li class="list-group-item">
                                <strong>${data.comment.user}:</strong> ${data.comment.content} 
                                <strong>Date:</strong> ${data.comment.created_at}
                            </li>
                        `;
                        modalBody.appendChild(newComment);
                    }

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
