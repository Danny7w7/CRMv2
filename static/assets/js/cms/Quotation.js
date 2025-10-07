// Autocompletar estado por ZIP
document.addEventListener("DOMContentLoaded", function () {
    const zipInput = document.getElementById('zipcode');
    if (zipInput) {
        zipInput.addEventListener('input', function () {
            const zipcode = this.value.trim();

            if (zipcode.length === 5) {
                fetch(`https://api.zippopotam.us/us/${zipcode}`)
                    .then(response => {
                        if (!response.ok) throw new Error("ZIP Code no encontrado");
                        return response.json();
                    })
                    .then(data => {
                        const state = data.places[0]['state abbreviation'];
                        document.getElementById('estado').value = state;
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        limpiarEstado();
                    });
            } else {
                limpiarEstado();
            }
        });
    }

    function limpiarEstado() {
        const estadoInput = document.getElementById('estado');
        if (estadoInput) estadoInput.value = "";
    }

    // Restaurar dependientes después del POST
    restaurarDependientes();
});

// Agregar dependientes dinámicamente
let contador = 1;

function agregarDependiente() {
    const div = document.createElement('div');
    div.className = 'col-12 dependiente-container';
    div.setAttribute('data-dependiente', contador);
    
    div.innerHTML = `
        <div class="border rounded p-3 mb-3">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0 fw-bold">Dependiente ${contador}</h6>
                <button type="button" class="btn btn-danger btn-sm" onclick="eliminarDependiente(this)">
                    Delete
                </button>
            </div>

            <div class="row g-3">
                <div class="col-12 col-lg-4">
                    <label class="form-label">Edad</label>
                    <input class="form-control" type="number" name="edad_${contador}" required>
                </div>

                <div class="col-12 col-lg-4">
                    <label class="form-label">Género:</label>					
                    <select class="form-select" name="genero_${contador}" required>
                        <option value="no_valid" disabled selected>Please Select</option>
                        <option value="Female">Femenino</option>
                        <option value="Male">Masculino</option>
                    </select>
                </div>

                <div class="col-12 col-lg-4">
                    <label class="form-label">¿Usa tabaco?</label> 
                    <select class="form-select" name="tabaco_${contador}" required>
                        <option value="no_valid" disabled selected>Please Select</option>
                        <option value="on">YES</option>
                        <option value="">NO</option>
                    </select>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById("dependientes").appendChild(div);
    contador++;
}

function eliminarDependiente(button) {
    const dependienteDiv = button.closest('.dependiente-container');
    if (dependienteDiv) {
        dependienteDiv.remove();
        actualizarNumerosDependientes();
    }
}

function actualizarNumerosDependientes() {
    const dependientes = document.querySelectorAll('.dependiente-container');
    dependientes.forEach((dep, index) => {
        const heading = dep.querySelector('h6');
        if (heading) {
            heading.textContent = `Dependiente ${index + 1}`;
        }
    });
}

// Formatear input tipo SSN (123-45-6789)
function formatInput(input) {
    let value = input.value.replace(/\D/g, '');

    if (value.length > 3 && value.length <= 5) {
        value = value.slice(0, 3) + '-' + value.slice(3);
    } else if (value.length > 5) {
        value = value.slice(0, 3) + '-' + value.slice(3, 5) + '-' + value.slice(5, 9);
    }

    input.value = value;
}

function restaurarDependientes() {
    const contenedorDependientes = document.getElementById('dependientes');
    if (!contenedorDependientes) return;
    
    const edadInputs = contenedorDependientes.querySelectorAll('input[type="hidden"][name^="edad_"]');
    
    edadInputs.forEach(input => {
        const name = input.getAttribute('name');
        const match = name.match(/edad_(\d+)/);
        
        if (match) {
            const index = parseInt(match[1]);
            if (index > 0) {
                const edad = input.value;
                const generoInput = contenedorDependientes.querySelector(`input[type="hidden"][name="genero_${index}"]`);
                const tabacoInput = contenedorDependientes.querySelector(`input[type="hidden"][name="tabaco_${index}"]`);
                
                if (edad && generoInput && tabacoInput) {
                    const genero = generoInput.value;
                    const tabaco = tabacoInput.value;
                    
                    const div = document.createElement('div');
                    div.className = 'col-12 dependiente-container';
                    div.setAttribute('data-dependiente', index);
                    
                    div.innerHTML = `
                        <div class="border rounded p-3 mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-3">
                                <h6 class="mb-0 fw-bold">Dependiente ${index}</h6>
                                <button type="button" class="btn btn-danger btn-sm" onclick="eliminarDependiente(this)">
                                    🗑️ Eliminar
                                </button>
                            </div>
                            <div class="row g-3">
                                <div class="col-12 col-lg-4">
                                    <label class="form-label">Edad</label>
                                    <input class="form-control" type="number" name="edad_${index}" required value="${edad}">
                                </div>
                                <div class="col-12 col-lg-4">
                                    <label class="form-label">Género:</label>					
                                    <select class="form-select" name="genero_${index}" required>
                                        <option value="no_valid" disabled>Please Select</option>
                                        <option value="Female" ${genero === 'Female' ? 'selected' : ''}>Femenino</option>
                                        <option value="Male" ${genero === 'Male' ? 'selected' : ''}>Masculino</option>
                                    </select>
                                </div>
                                <div class="col-12 col-lg-4">
                                    <label class="form-label">¿Usa tabaco?</label> 
                                    <select class="form-select" name="tabaco_${index}" required>
                                        <option value="no_valid" disabled>Please Select</option>
                                        <option value="on" ${tabaco === 'on' ? 'selected' : ''}>YES</option>
                                        <option value="" ${tabaco === '' ? 'selected' : ''}>NO</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    contenedorDependientes.appendChild(div);
                    if (index >= contador) contador = index + 1;
                    
                    input.remove();
                    generoInput.remove();
                    tabacoInput.remove();
                }
            }
        }
    });
    
    actualizarNumerosDependientes();
}
