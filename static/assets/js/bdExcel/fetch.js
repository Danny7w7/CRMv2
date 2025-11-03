// ============================================
// Archivo: static/js/bd_table.js
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Obtener configuración del dataset del elemento contenedor
    const container = document.getElementById('bdTableContainer');
    if (!container) {
        console.error('No se encontró el contenedor #bdTableContainer');
        return;
    }
    
    const isAdmin = container.dataset.isAdmin === 'true';
    const bdFilter = container.dataset.bdFilter || '';
    const apiUrl = container.dataset.apiUrl;
    
    let currentPage = 1;
    let recordsPerPage = 50;
    let searchTerm = '';
    let totalRecords = 0;
    
    // Referencias a elementos
    const tableBody = document.getElementById('tableBody');
    const tableInfo = document.getElementById('tableInfo');
    const pagination = document.getElementById('pagination');
    const searchInput = document.getElementById('searchInput');
    const recordsSelect = document.getElementById('recordsPerPage');
    
    // Debounce para búsqueda
    let searchTimeout;
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchTerm = this.value;
            currentPage = 1;
            loadData();
        }, 500);
    });
    
    // Cambio de registros por página
    recordsSelect.addEventListener('change', function() {
        recordsPerPage = parseInt(this.value);
        currentPage = 1;
        loadData();
    });
    
    // Función principal para cargar datos
    async function loadData() {
        try {
            // Mostrar loading
            tableBody.innerHTML = `
                <tr>
                    <td colspan="${isAdmin ? 11 : 10}" class="text-center">
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">Cargando...</span>
                        </div>
                    </td>
                </tr>
            `;
            
            // Construir URL con parámetros
            const params = new URLSearchParams({
                draw: Date.now(),
                start: (currentPage - 1) * recordsPerPage,
                length: recordsPerPage,
                'search[value]': searchTerm,
                bd_filter: bdFilter
            });
            
            const response = await fetch(`${apiUrl}?${params}`);
            
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            
            totalRecords = data.recordsTotal;
            renderTable(data.data);
            renderPagination();
            renderInfo();
            
        } catch (error) {
            console.error('Error al cargar datos:', error);
            tableBody.innerHTML = `
                <tr>
                    <td colspan="${isAdmin ? 11 : 10}" class="text-center text-danger">
                        Error al cargar los datos. Por favor, intente de nuevo.
                    </td>
                </tr>
            `;
            
            // SweetAlert para error de carga
            Swal.fire({
                icon: 'error',
                title: 'Error al cargar datos',
                text: 'No se pudieron cargar los registros. Por favor, intente de nuevo.',
                confirmButtonColor: '#d33'
            });
        }
    }
    
    // Renderizar filas de la tabla
    function renderTable(data) {
        if (data.length === 0) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="${isAdmin ? 11 : 10}" class="text-center">
                        No se encontraron resultados
                    </td>
                </tr>
            `;
            return;
        }
        
        // Obtener CSRF token UNA VEZ fuera del loop
        const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfTokenElement ? csrfTokenElement.value : '';
        const optionsBd = window.BD_OPTIONS || []; // Las opciones deben pasarse desde el template
        
        tableBody.innerHTML = data.map(item => {
            let row = '<tr>';
            
            // Columna Sold (solo para Admin)
            if (isAdmin) {
                row += `
                    <td style="vertical-align: middle;">
                        ${item.is_sold 
                            ? '<div class="font-35 text-success"><i class="bx bxs-check-circle"></i></div>'
                            : '<div class="font-35 text-danger"><i class="bx bxs-message-square-x"></i></div>'
                        }
                    </td>
                `;
            }
            
            // Datos básicos
            row += `
                <td style="vertical-align: middle;">${item.first_name}</td>
                <td style="vertical-align: middle;">${item.last_name}</td>
                <td style="vertical-align: middle;">${item.phone}</td>
                <td style="vertical-align: middle;">${item.address}</td>
                <td style="vertical-align: middle;">${item.city}</td>
                <td style="vertical-align: middle;">${item.state}</td>
            `;
            
            // Other Information
            row += `
                <td style="vertical-align: middle;">
                    <button type="button" class="btn btn-outline-primary btn-view-other" 
                            data-other='${item.pretty_other ? JSON.stringify(item.pretty_other) : "null"}'>
                        <i class='bx bx-info-circle me-0'></i>
                    </button>
                </td>
            `;
                    
            // Typification
            row += `
                <td style="vertical-align: middle;">
                    <form method="POST" class="form-observation" data-id="${item.id}">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                        <input type="hidden" name="record_id" value="${item.id}">
                        <input type="hidden" name="record_id_coment" value="${item.excel_metadata}">
                        <select name="observation" class="form-select">
                            <option value="no_valid" disabled selected>Please Select</option>
                            ${optionsBd.map(opt => `<option value="${opt}">${opt}</option>`).join('')}
                        </select>
                        <button type="submit" class="btn btn-sm btn-secondary mt-1">Save</button>
                    </form>
                </td>
            `;
            
            // View Typification
            row += `
                <td style="vertical-align: middle;">
                    <button type="button" class="btn btn-outline-secondary btn-view-comment" 
                            data-id="${item.id}">
                        <i class='bx bx-comment-detail me-0'></i>
                    </button>

                    <button type="button" class="btn btn-warning btn-sm btn-add-observation"
                            data-id="${item.id}" data-excel="${item.excel_metadata}" data-text="${item.observation || ''}">
                        <i class='bx bx-edit-alt'></i>
                    </button>

                </td>
            `;
            
            row += '</tr>';
            return row;
        }).join('');
        
        // Agregar event listeners a los botones
        attachEventListeners();
    }
    
    // Renderizar información
    function renderInfo() {
        const start = (currentPage - 1) * recordsPerPage + 1;
        const end = Math.min(currentPage * recordsPerPage, totalRecords);
        tableInfo.textContent = `Mostrando ${start} a ${end} de ${totalRecords} registros`;
    }
    
    // Renderizar paginación
    function renderPagination() {
        const totalPages = Math.ceil(totalRecords / recordsPerPage);
        
        if (totalPages <= 1) {
            pagination.innerHTML = '';
            return;
        }
        
        let html = '';
        
        // Botón Primera
        html += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="1">Primera</a>
            </li>
        `;
        
        // Botón Anterior
        html += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage - 1}">Anterior</a>
            </li>
        `;
        
        // Páginas numeradas (mostrar 5 páginas alrededor de la actual)
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, currentPage + 2);
        
        for (let i = startPage; i <= endPage; i++) {
            html += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
        
        // Botón Siguiente
        html += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage + 1}">Siguiente</a>
            </li>
        `;
        
        // Botón Última
        html += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${totalPages}">Última</a>
            </li>
        `;
        
        pagination.innerHTML = html;
        
        // Event listeners para paginación
        pagination.querySelectorAll('a.page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                if (!this.parentElement.classList.contains('disabled') && 
                    !this.parentElement.classList.contains('active')) {
                    currentPage = parseInt(this.dataset.page);
                    loadData();
                }
            });
        });
    }
    
    // Agregar event listeners a botones dinámicos
    function attachEventListeners() {
        // Botones "Other Information"
        document.querySelectorAll('.btn-view-other').forEach(btn => {
            btn.addEventListener('click', function() {
                const otherData = JSON.parse(this.dataset.other);
                showOtherModal(otherData);
            });
        });
        
        // Botones "View Typification"
        document.querySelectorAll('.btn-view-comment').forEach(btn => {
            btn.addEventListener('click', function() {
                const recordId = this.dataset.id;
                showCommentModal(recordId);
            });
        });
        
        // Formularios de typification
        document.querySelectorAll('.form-observation').forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault();
                saveObservation(this);
            });
        });

        // Botón abrir modal observación
        document.querySelectorAll('.btn-add-observation').forEach(btn => {
            btn.addEventListener('click', function() {
                const id = this.dataset.id;
                const text = this.dataset.text;

                document.getElementById("obsRecordId").value = id;
                document.getElementById("obsInput").value = text;
                document.getElementById("obsExcelId").value = this.dataset.excel; 

                new bootstrap.Modal(document.getElementById('modalObservation')).show();
            });
        });
    }
    
    // Mostrar modal de "Other"
    function showOtherModal(data) {
        const modalBody = document.getElementById('modalOtherBody');
        
        // Verificar si data es string "null" o realmente null/undefined
        if (!data || data === 'null' || data === null || (typeof data === 'object' && Object.keys(data).length === 0)) {
            modalBody.innerHTML = '<p class="text-muted">Sin datos adicionales.</p>';
        } else {
            let html = '<table class="table table-sm table-bordered"><tbody>';
            for (const [key, value] of Object.entries(data)) {
                // Convertir null a texto legible
                const displayValue = value === null || value === undefined ? '<em class="text-muted">Sin datos</em>' : value;
                html += `<tr><th>${key}</th><td>${displayValue}</td></tr>`;
            }
            html += '</tbody></table>';
            modalBody.innerHTML = html;
        }
        
        const modal = new bootstrap.Modal(document.getElementById('modalOther'));
        modal.show();
    }
    
    // Mostrar modal de comentarios/tipificaciones
    async function showCommentModal(recordId) {
        const modalBody = document.getElementById('modalVerTextoBody');
        const modal = new bootstrap.Modal(document.getElementById('modalVerTexto'));
        
        // Mostrar loading
        modalBody.innerHTML = `
            <div class="text-center">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Cargando...</span>
                </div>
            </div>
        `;
        
        modal.show();
        
        try {
            // Hacer petición para obtener los comentarios
            const response = await fetch(`${apiUrl}?get_comments=1&record_id=${recordId}`);
            
            if (!response.ok) {
                throw new Error('Error al cargar comentarios');
            }
            
            const data = await response.json();
            
            if (data.comments && data.comments.length > 0) {
                let html = '<div class="list-group">';
                data.comments.forEach(comment => {
                    html += `
                        <div class="list-group-item">
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1">${comment.agent_name || 'Usuario'}</h6>
                                <small>${comment.date || ''}</small>
                            </div>
                            <p class="mb-1">${comment.text || ''}</p>
                            ${comment.type ? `<small class="text-muted"><span class="badge bg-info">${comment.type}</span></small>` : ''}
                        </div>
                    `;
                });
                html += '</div>';
                modalBody.innerHTML = html;
            } else {
                modalBody.innerHTML = '<p class="text-muted">No hay comentarios para este registro.</p>';
            }
            
        } catch (error) {
            console.error('Error:', error);
            modalBody.innerHTML = '<p class="text-danger">Error al cargar los comentarios.</p>';
            
            // SweetAlert para error de comentarios
            Swal.fire({
                icon: 'error',
                title: 'Error',
                text: 'No se pudieron cargar los comentarios',
                confirmButtonColor: '#d33'
            });
        }
    }
    
    // Guardar observación (tipificación)
    async function saveObservation(form) {
        const formData = new FormData(form);
        const button = form.querySelector('button[type="submit"]');
        const originalText = button.textContent;
        
        button.disabled = true;
        button.textContent = 'Guardando...';
        
        try {
            const response = await fetch(apiUrl, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                // SweetAlert de éxito
                Swal.fire({
                    icon: 'success',
                    title: '¡Guardado!',
                    text: 'Tipificación guardada exitosamente',
                    timer: 2000,
                    showConfirmButton: false,
                    toast: true,
                    position: 'top-end'
                });
                
                form.querySelector('select').value = 'no_valid';
            } else {
                // SweetAlert de error
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: data.error || 'Error desconocido al guardar',
                    confirmButtonColor: '#d33'
                });
            }
        } catch (error) {
            console.error('Error:', error);
            
            // SweetAlert de error de red
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'No se pudo guardar la tipificación. Verifique su conexión.',
                confirmButtonColor: '#d33'
            });
        } finally {
            button.disabled = false;
            button.textContent = originalText;
        }
    }

    // Guardar observación (nota adicional)
    document.getElementById("btnSaveObs").addEventListener("click", async () => {
        const id = document.getElementById("obsRecordId").value;
        const text = document.getElementById("obsInput").value;
        const excelId = document.getElementById("obsExcelId").value;
        const csrf = document.querySelector("[name=csrfmiddlewaretoken]").value;

        // Validar que el texto no esté vacío
        if (!text.trim()) {
            Swal.fire({
                icon: 'warning',
                title: 'Campo vacío',
                text: 'Por favor escriba una observación antes de guardar',
                confirmButtonColor: '#ffc107'
            });
            return;
        }

        // Mostrar loading mientras guarda
        Swal.fire({
            title: 'Guardando...',
            text: 'Por favor espere',
            allowOutsideClick: false,
            allowEscapeKey: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        const formData = new FormData();
        formData.append("record_id", id);
        formData.append("record_id_coment", excelId);
        formData.append("observation", text);
        formData.append("type", "observation");

        try {
            const response = await fetch(apiUrl, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrf,
                    "X-Requested-With": "XMLHttpRequest"
                },
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                // Cerrar modal
                bootstrap.Modal.getInstance(document.getElementById('modalObservation')).hide();
                
                // Limpiar campo
                document.getElementById("obsInput").value = "";
                
                // SweetAlert de éxito
                Swal.fire({
                    icon: 'success',
                    title: '¡Excelente!',
                    text: 'Observación guardada correctamente',
                    timer: 2000,
                    showConfirmButton: false
                });
                
                // Recargar datos
                loadData();
            } else {
                // SweetAlert de error
                Swal.fire({
                    icon: 'error',
                    title: 'Error al guardar',
                    text: data.error || 'Ocurrió un error desconocido',
                    confirmButtonColor: '#d33'
                });
            }
        } catch (error) {
            console.error('Error:', error);
            
            // SweetAlert de error de conexión
            Swal.fire({
                icon: 'error',
                title: 'Error de conexión',
                text: 'No se pudo conectar con el servidor',
                confirmButtonColor: '#d33'
            });
        }
    });
    
    // Cargar datos iniciales
    loadData();
});