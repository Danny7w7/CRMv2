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
});

// Agregar dependientes dinámicamente
let contador = 1;

function agregarDependiente() {
    const div = document.createElement('div');
    div.innerHTML = `
        <legend>Dependiente ${contador}</legend>

        <div class="col-12 col-lg-4">
            <label class="form-label">Edad</label>
            <input class="form-control" type="number" name="edad_${contador}" required>
        </div>

        <div class="col-12 col-lg-4">
            <label class="form-label">Género:</label>					
            <select class="form-select" name="genero_${contador}">
                <option value="no_valid" disabled selected>Please Select</option>
                <option value="Female">Femenino</option>
                <option value="Male">Masculino</option>
            </select>
        </div>
        <div class="col-12 col-lg-4">
            <label class="form-label">¿Usa tabaco?</label> 
            <select class="form-select" name="tabaco_${contador}">
                <option value="no_valid" disabled selected>Please Select</option>
                <option value="on">YES</option>
                <option value="">NO</option>
            </select>
        </div>
        <br>
    `;
    document.getElementById("dependientes").appendChild(div);
    contador++;
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
