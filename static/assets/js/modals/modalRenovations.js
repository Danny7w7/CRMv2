// Script para manejar la carga de dependientes en el modal
document.addEventListener('DOMContentLoaded', function() {
    const renovationModal = document.getElementById('renovationModal');
    
    renovationModal.addEventListener('shown.bs.modal', function () {
        // Solo calcular edad automáticamente cuando cambie la fecha de nacimiento
        setupBirthDateCalculation();
    });
    
    // Variable para contar dependientes dinámicos
    let dependentCounter = 0;
    
    // Función para formatear fecha para Flatpickr (convertir Y-m-d a m/d/Y)
    function formatDateForFlatpickr(dateString) {
        if (!dateString) return '';
        
        // Si ya está en formato m/d/Y, devolverlo como está
        if (dateString.includes('/')) return dateString;
        
        // Si está en formato Y-m-d, convertir a m/d/Y
        const parts = dateString.split('-');
        if (parts.length === 3) {
            const [year, month, day] = parts;
            return `${month}/${day}/${year}`;
        }
        
        return dateString;
    }
    
    // Función para convertir fecha de m/d/Y a Date object
    function parseDateFromFlatpickr(dateString) {
        if (!dateString) return null;
        
        // Si está en formato m/d/Y
        if (dateString.includes('/')) {
            const [month, day, year] = dateString.split('/');
            return new Date(year, month - 1, day); // month - 1 porque Date usa 0-11 para meses
        }
        
        // Si está en otro formato, intentar parsearlo directamente
        return new Date(dateString);
    }
    
    // Función para inicializar Flatpickr en elementos específicos
    function initializeFlatpickr(selector) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(element => {
            if (!element._flatpickr) { // Evitar inicializar dos veces
                flatpickr(element, {
                    dateFormat: "m/d/Y",
                    allowInput: true,
                    onChange: function(selectedDates, dateStr, instance) {
                        // Trigger manual change event para el cálculo de edad
                        const event = new Event('change', { bubbles: true });
                        instance.element.dispatchEvent(event);
                    }
                });
            }
        });
    }
    function createDependentHTML(index, data = {}, isExisting = false) {
        const dependentId = isExisting ? data.id : `new_${Date.now()}_${index}`;
        
        return `
            <div class="row g-3 mb-3 p-3 border rounded bg-light dependent-row" data-dependent-index="${index}">
                <div class="col-12 d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0 text-primary">Dependiente #${index}</h6>
                    <button type="button" class="btn btn-danger btn-sm" onclick="removeDependent(this)">
                        <i class="bi bi-trash me-1"></i>Eliminar
                    </button>
                </div>
                
                ${isExisting ? `<input type="hidden" name="renovation_dependent_id_${dependentId}" value="${data.id}">` : ''}
                <input type="hidden" name="renovation_dependent_index_${dependentId}" value="${index}">
                
                <div class="col-12 col-lg-6">
                    <label class="form-label">Name of Dependent</label>
                    <input type="text" class="form-control" name="renovation_dependent_name_${dependentId}" value="${data.name || ''}" required>
                </div>
                
                <div class="col-12 col-lg-3">
                    <label class="form-label">Apply</label>
                    <select class="form-select" name="renovation_dependent_apply_${dependentId}" required>
                        <option value="" disabled ${!data.apply ? 'selected' : ''}>Please Select</option>
                        <option value="YES" ${data.apply === 'YES' ? 'selected' : ''}>YES</option>
                        <option value="NO" ${data.apply === 'NO' ? 'selected' : ''}>NO</option>
                    </select>
                </div>
                
                <div class="col-12 col-lg-3">
                    <label class="form-label">Sex</label>
                    <select class="form-select" name="renovation_dependent_sex_${dependentId}" required>
                        <option value="" disabled ${!data.sex ? 'selected' : ''}>Please Select</option>
                        <option value="M" ${data.sex === 'M' ? 'selected' : ''}>MALE</option>
                        <option value="F" ${data.sex === 'F' ? 'selected' : ''}>FEMALE</option>
                    </select>
                </div>
                
                <div class="col-12 col-lg-4">
                    <label class="form-label">Relationship</label>
                    <select class="form-select" name="renovation_dependent_kinship_${dependentId}">
                        <option value="" disabled ${!data.kinship ? 'selected' : ''}>Please Select</option>
                        <option value="DAD" ${data.kinship === 'DAD' ? 'selected' : ''}>DAD</option>
                        <option value="MOM" ${data.kinship === 'MOM' ? 'selected' : ''}>MOM</option>
                        <option value="SON" ${data.kinship === 'SON' ? 'selected' : ''}>SON</option>
                        <option value="DAUGHTER" ${data.kinship === 'DAUGHTER' ? 'selected' : ''}>DAUGHTER</option>
                        <option value="GRANDPARENT" ${data.kinship === 'GRANDPARENT' ? 'selected' : ''}>GRANDPARENT</option>
                        <option value="GRANDMOTHER" ${data.kinship === 'GRANDMOTHER' ? 'selected' : ''}>GRANDMOTHER</option>
                        <option value="COUPLE" ${data.kinship === 'COUPLE' ? 'selected' : ''}>COUPLE</option>
                        <option value="UNKNOWN" ${data.kinship === 'UNKNOWN' ? 'selected' : ''}>UNKNOWN</option>
                    </select>
                </div>
                
                <div class="col-12 col-lg-4">
                    <label class="form-label">Date Birth</label>
                    <input type="text" class="form-control dependent-birth-date flatpickr-date" name="renovation_dependent_birth_${dependentId}" value="${data.date_birth ? formatDateForFlatpickr(data.date_birth) : ''}">
                </div>
                
                <div class="col-12 col-lg-4">
                    <label class="form-label">Migration Status</label>
                    <select class="form-select" name="renovation_dependent_migration_${dependentId}" required>
                        <option value="" disabled ${!data.migration_status ? 'selected' : ''}>Please Select</option>
                        <option value="EMPLOYMENT AUTHORIZATION" ${data.migration_status === 'EMPLOYMENT AUTHORIZATION' ? 'selected' : ''}>Employment Authorization</option>
                        <option value="NOTICE OF ACTION" ${data.migration_status === 'NOTICE OF ACTION' ? 'selected' : ''}>Notice of Action (i-797)</option>
                        <option value="REFUGEE" ${data.migration_status === 'REFUGEE' ? 'selected' : ''}>Refugee</option>
                        <option value="ASYLUM" ${data.migration_status === 'ASYLUM' ? 'selected' : ''}>Asylum</option>
                        <option value="TPS" ${data.migration_status === 'TPS' ? 'selected' : ''}>Temporary Protection Status (TPS)</option>
                        <option value="DOMESTIC VIOLENCE" ${data.migration_status === 'DOMESTIC VIOLENCE' ? 'selected' : ''}>Domestic Violence</option>
                        <option value="PERMANENT RESIDENT" ${data.migration_status === 'PERMANENT RESIDENT' ? 'selected' : ''}>Permanent Resident (Green Card)</option>
                        <option value="CONDITIONAL RESIDENT" ${data.migration_status === 'CONDITIONAL RESIDENT' ? 'selected' : ''}>Conditional Resident</option>
                        <option value="PAROLE" ${data.migration_status === 'PAROLE' ? 'selected' : ''}>Parole</option>
                        <option value="US CITIZEN" ${data.migration_status === 'US CITIZEN' ? 'selected' : ''}>US Citizen (Driver's License)</option>
                        <option value="STUDENT VISA" ${data.migration_status === 'STUDENT VISA' ? 'selected' : ''}>Student Visa (I-20)</option>
                        <option value="CURRENTLY IN PROCESS" ${data.migration_status === 'CURRENTLY IN PROCESS' ? 'selected' : ''}>Currently In Process</option>
                        <option value="UNKNOWN" ${data.migration_status === 'UNKNOWN' ? 'selected' : ''}>UNKNOWN</option>
                    </select>
                </div>
            </div>
        `;
    }
    
    // Función para agregar un nuevo dependiente
    window.addNewDependent = function() {
        dependentCounter++;
        const container = document.getElementById('dependentsContainer');
        const newDependentHTML = createDependentHTML(dependentCounter);
        
        container.insertAdjacentHTML('beforeend', newDependentHTML);
        
        // Configurar eventos para el nuevo dependiente (incluyendo Flatpickr)
        setupDependentEvents();
        updateDependentNumbers();
        
        showAlert('Dependiente agregado correctamente', 'success');
    };
    
    // Función para eliminar un dependiente
    window.removeDependent = function(button) {
        const dependentRow = button.closest('.dependent-row');
        const dependentName = dependentRow.querySelector('input[name*="name"]').value || 'Sin nombre';
        
        if (confirm(`¿Estás seguro de que quieres eliminar al dependiente "${dependentName}"?`)) {
            dependentRow.remove();
            updateDependentNumbers();
            showAlert('Dependiente eliminado correctamente', 'info');
        }
    };
    
    // Función para actualizar la numeración de dependientes
    function updateDependentNumbers() {
        const dependentRows = document.querySelectorAll('.dependent-row');
        dependentRows.forEach((row, index) => {
            const header = row.querySelector('h6');
            if (header) {
                header.textContent = `Dependiente #${index + 1}`;
            }
            row.setAttribute('data-dependent-index', index + 1);
        });
    }
    
    // Función para configurar eventos de dependientes
    function setupDependentEvents() {
        // Inicializar Flatpickr en todos los campos de fecha de dependientes
        initializeFlatpickr('.dependent-birth-date');
        
        // Configurar cálculo de edad para todos los dependientes
        const dependentBirthDates = document.querySelectorAll('.dependent-birth-date');
        dependentBirthDates.forEach(input => {
            // Remover eventos anteriores para evitar duplicados
            input.removeEventListener('change', calculateDependentAge);
            input.addEventListener('change', calculateDependentAge);
        });
    }
    
    // Función para calcular edad de dependiente
    function calculateDependentAge(event) {
        const birthDateInput = event.target;
        const dependentRow = birthDateInput.closest('.dependent-row');
        const ageInput = dependentRow.querySelector('.dependent-age');
        
        if (birthDateInput.value && ageInput) {
            // Usar la función para parsear fecha de Flatpickr
            const birthDate = parseDateFromFlatpickr(birthDateInput.value);
            
            if (birthDate) {
                const today = new Date();
                let age = today.getFullYear() - birthDate.getFullYear();
                const monthDiff = today.getMonth() - birthDate.getMonth();
                
                if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
                    age--;
                }
                
                ageInput.value = age >= 0 ? age : '';
            }
        }
    }
    
    function setupBirthDateCalculation() {
        // Inicializar Flatpickr en el campo principal
        initializeFlatpickr('#renovation_date_birth');
        
        // Cálculo de edad para el cliente principal
        const birthDateInput = document.getElementById('renovation_date_birth');
        const ageInput = document.getElementById('renovation_old');
        
        if (birthDateInput && ageInput) {
            birthDateInput.addEventListener('change', function() {
                // Usar la función para parsear fecha de Flatpickr
                const birthDate = parseDateFromFlatpickr(this.value);
                
                if (birthDate) {
                    const today = new Date();
                    let age = today.getFullYear() - birthDate.getFullYear();
                    const monthDiff = today.getMonth() - birthDate.getMonth();
                    
                    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) {
                        age--;
                    }
                    
                    ageInput.value = age >= 0 ? age : '';
                }
            });
        }
        
        // Configurar eventos para dependientes existentes y nuevos
        setupDependentEvents();
    }
    
    // Validación del formulario antes de enviar
    const renovationForm = document.getElementById('renovationForm');
    if (renovationForm) {
        renovationForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validaciones personalizadas
            if (validateRenovationForm()) {
                // Si pasa todas las validaciones, enviar el formulario
                this.submit();
            }
        });
    }
    
    function validateRenovationForm() {
        let isValid = true;
        const requiredFields = renovationForm.querySelectorAll('[required]');
        
        // Limpiar errores previos
        document.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        
        // Validar campos requeridos
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            }
        });
        
        // Validaciones específicas
        const email = document.getElementById('renovation_email');
        if (email && email.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email.value)) {
                email.classList.add('is-invalid');
                isValid = false;
                showAlert('Por favor, ingresa un email válido.', 'warning');
            }
        }
        
        const phone = document.getElementById('renovation_phone_number');
        if (phone && phone.value) {
            if (phone.value.length < 10) {
                phone.classList.add('is-invalid');
                isValid = false;
                showAlert('El número de teléfono debe tener al menos 10 dígitos.', 'warning');
            }
        }
        
        if (!isValid) {
            showAlert('Por favor, complete todos los campos requeridos correctamente.', 'danger');
        }
        
        return isValid;
    }
    
    function showAlert(message, type = 'info') {
        // Crear alerta temporal
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 350px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto-remover después de 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
    
    // Manejar cambios en el código postal para autocompletar ciudad y estado
    const zipcodeInput = document.getElementById('renovation_zipcode');
    if (zipcodeInput) {
        zipcodeInput.addEventListener('blur', function() {
            const zipcode = this.value;
            if (zipcode && zipcode.length === 5) {
                // Aquí puedes hacer una llamada AJAX para obtener ciudad y estado
                fetchLocationByZipcode(zipcode);
            }
        });
    }
    
    function fetchLocationByZipcode(zipcode) {
        // Ejemplo de llamada AJAX (ajusta la URL según tu implementación)
        fetch(`/api/location/${zipcode}/`)
            .then(response => response.json())
            .then(data => {
                if (data.city) {
                    document.getElementById('renovation_city').value = data.city;
                }
                if (data.state) {
                    document.getElementById('renovation_state').value = data.state;
                }
                if (data.county) {
                    document.getElementById('renovation_county').value = data.county;
                }
            })
            .catch(error => {
                //console.log('Error fetching location:', error);
            });
    }
    
    // Función para cargar dependientes existentes desde el servidor
    function loadExistingDependents(dependents) {
        
        // Primero crear la estructura base si no existe
        const renovationDependents = document.getElementById('renovationDependents');
        if (!renovationDependents) {
            //console.error('No se encontró el contenedor renovationDependents');
            return;
        }
        
        // Crear la estructura completa con los dependientes existentes
        let dependentsHTML = `
            <hr>
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="text-success border-bottom pb-2 mb-0">Dependientes</h4>
                <div>
                    <button type="button" class="btn btn-success btn-sm me-2" onclick="addNewDependent()">
                        <i class="bi bi-plus-circle me-1"></i>Agregar Dependiente
                    </button>
                </div>
            </div>
            <div id="dependentsContainer">
        `;
        
        // Agregar cada dependiente existente
        dependentCounter = 0;
        dependents.forEach((dependent, index) => {
            dependentCounter++;
            dependentsHTML += createDependentHTML(dependentCounter, dependent, true);
        });
        
        dependentsHTML += '</div>';
        
        // Insertar todo el HTML en renovationDependents
        renovationDependents.innerHTML = dependentsHTML;
        
        // Configurar eventos para todos los dependientes
        setupDependentEvents();
      
    }
    
    // Exponer función para uso desde HTML
    window.loadExistingDependents = loadExistingDependents;
    
    // Copiar información del formulario original al modal (opcional)
    function copyOriginalFormData() {
        // Esta función puede copiar datos específicos del formulario original
        // si necesitas sincronizar alguna información adicional
    }
    
    // Limpiar formulario cuando se cierre el modal
    renovationModal.addEventListener('hidden.bs.modal', function () {
        const renovationForm = document.getElementById('renovationForm');
        if (renovationForm) {
            renovationForm.reset();
        }
        dependentCounter = 0;
        document.querySelectorAll('.is-invalid').forEach(field => {
            field.classList.remove('is-invalid');
        });
        
        // Limpiar dependientes dinámicos
        const dependentsContainer = document.getElementById('dependentsContainer');
        if (dependentsContainer) {
            dependentsContainer.innerHTML = '';
        }
    });
});