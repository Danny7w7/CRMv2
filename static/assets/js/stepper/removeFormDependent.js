function removeDependent(button) {
    // Obtener el contenedor del dependiente (div padre)
    const dependentDiv = button.closest('.dependentClassList');
    const dependentId = dependentDiv.querySelector('[name="dependentId"]').value;
    const company = dependentDiv.querySelector('[name="company"]').value;
 

    // Confirmar antes de eliminar
    if (dependentId && confirm("Are you sure you want to delete this dependent?")) {
        const formData = new FormData();
        formData.append('dependentId', dependentId);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        // Realizar la solicitud fetch para eliminar el registro
        fetch(`/formCreatePlan/${company}/deleteDependent/${dependentId}/`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Eliminar el div del dependiente del DOM si se eliminó correctamente en la BD
                dependentDiv.remove();
                console.log('Dependent deleted successfully');
            } else {
                console.error('Error deleting dependent:', data.error);
                alert('Error deleting dependent');
            }
        })
        .catch(error => {
            console.error('Request failed:', error);
            alert('Request failed');
        });
    } else if (!dependentId) {
        // Si no hay un ID, solo elimina el div del DOM (caso de dependientes nuevos no guardados)
        dependentDiv.remove();
    }
}

function removeSupp(button) {
    // Obtener el contenedor del dependiente (div padre)
    const suppDiv = button.closest('.supplementaryClassList');
    const suppId = suppDiv.querySelector('[name="suppId"]').value;
    const company = suppDiv.querySelector('[name="company"]').value;

    // Confirmar antes de eliminar
    if (suppId && confirm("Are you sure you want to delete this SUPPLEMENTARY?")) {
        const formData = new FormData();
        formData.append('suppId', suppId);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);

        // Realizar la solicitud fetch para eliminar el registro
        fetch(`/formCreatePlan/${company}/deleteSupp/${suppId}/`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Eliminar el div del dependiente del DOM si se eliminó correctamente en la BD
                suppDiv.remove();
                console.log('supp deleted successfully');
            } else {
                console.error('Error deleting dependent:', data.error);
                alert('Error deleting dependent');
            }
        })
        .catch(error => {
            console.error('Request failed:', error);
            alert('Request failed');
        });
    } else if (!suppId) {
        // Si no hay un ID, solo elimina el div del DOM (caso de dependientes nuevos no guardados)
        suppDiv.remove();
    }
}