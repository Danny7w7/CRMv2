// Función para obtener el token CSRF desde las cookies
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = getCookie('csrftoken'); // Obtener el token CSRF
    const socialField = document.getElementById('social_security');
    const showButton = document.getElementById('show-full-social');
    const saveButton = document.getElementById('save-social');
    const blockButton = document.getElementById('block-social');
    const clientId = document.getElementById('social_security').dataset.clientId; // 🔹 Obtener `client_id` desde `data-client-id`

    function enableEditing() {
        socialField.removeAttribute('disabled');
        socialField.focus();
        saveButton.hidden = false;
        blockButton.hidden = false;
        showButton.hidden = true;
    }

    function disableEditing() {
        socialField.setAttribute('disabled', true);
        saveButton.hidden = true;
        blockButton.hidden = true;
        showButton.hidden = false;
    }

    showButton.addEventListener('click', async () => {
        if (!socialField.value.trim()) {
            // Si el campo está vacío, permitir edición sin clave
            enableEditing();
        } else {
            // Solicitar clave con SweetAlert2
            const { value: password } = await Swal.fire({
                title: '🔑 Ingresa la clave',
                input: 'password',
                inputPlaceholder: 'Escribe la clave aquí...',
                inputAttributes: {
                    autocapitalize: 'off',
                    autocorrect: 'off'
                },
                showCancelButton: true,
                confirmButtonText: 'Desbloquear',
                cancelButtonText: 'Cancelar',
                confirmButtonColor: '#4CAF50',
                cancelButtonColor: '#d33',
                inputValidator: (value) => {
                    if (!value) {
                        return '⚠️ Debes ingresar una clave';
                    }
                }
            });

            if (password) {
                try {
                    const response = await fetch('/blockSocialSecurityLife/', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': csrfToken,
                        },
                        body: new URLSearchParams({
                            key: password,
                            action: 'validate_key',
                            client_id: clientId,
                        }),
                    });

                    if (!response.ok) {
                        Swal.fire('Error', `⚠️ ${response.statusText}`, 'error');
                        return;
                    }

                    const data = await response.json();

                    if (data.status === 'success') {

                        // 🔹 Si es "N/A", vaciar el campo
                        if (socialField.value.trim() === 'N/A') {
                            socialField.value = "";
                        } else {
                            socialField.value = formatSocialSecurityNumber(data.social);
                        }

                        enableEditing();
                    } else {
                        Swal.fire('Error', `❌ ${data.message}`, 'error');
                    }
                } catch (error) {
                    //console.error('❌ Error en la solicitud:', error);
                    Swal.fire('Error', '⚠️ Hubo un problema, intenta nuevamente.', 'error');
                }
            }
        }
    });

    saveButton.addEventListener('click', async () => {
        const newSocial = socialField.value.replace(/-/g, '').trim(); // Eliminar guiones antes de enviar

        if (newSocial.length !== 9 || isNaN(newSocial)) {
            Swal.fire('Error', '⚠️ El número de seguro social debe tener 9 dígitos.', 'error');
            return;
        }

        try {
            const response = await fetch('/blockSocialSecurityLife/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrfToken,
                },
                body: new URLSearchParams({
                    action: 'save_social',
                    new_social: newSocial,
                    client_id: clientId,
                }),
            });

            const data = await response.json();

            if (data.status === 'success') {
                Swal.fire({
                    icon: 'success',
                    title: '✅ Guardado',
                    text: `Número guardado correctamente.`,
                    confirmButtonColor: '#4CAF50'
                });

                // 🔹 Ocultar nuevamente el número en el campo
                socialField.value = `XXX-XX-${newSocial.slice(-4)}`;
                disableEditing(); // Deshabilita la edición del campo

            } else {
                Swal.fire('Error', `❌ ${data.message}`, 'error');
            }
        } catch (error) {
            //console.error('❌ Error en la solicitud:', error);
            Swal.fire('Error', '⚠️ No se pudo guardar. Intenta nuevamente.', 'error');
        }
    });

    blockButton.addEventListener('click', () => {

        // 🔹 Obtener el valor actual sin guiones
        const currentValue = socialField.value.replace(/-/g, '').trim();

        if (currentValue.length === 9 && !isNaN(currentValue)) {
            // 🔹 Reemplazar los primeros 5 dígitos con "XXX-XX-"
            socialField.value = `XXX-XX-${currentValue.slice(-4)}`;
        }

        Swal.fire({
            icon: 'info',
            title: '🔒 Número bloqueado',
            text: 'El campo ha sido bloqueado nuevamente.',
            confirmButtonColor: '#d33'
        });
        disableEditing();
    });

    function formatSocialSecurityNumber(number) {
        if (number.length === 9) {
            return `${number.slice(0, 3)}-${number.slice(3, 5)}-${number.slice(5)}`;
        }
        return number;
    }
});
