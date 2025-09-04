let campaigns = [];

function getListCampaigns() {
    fetch('/api/dialer/adminDashboard/campaigns/getList/', {
        method: 'GET'
    })
    .then(response => response.json())
    .then(data => {
        campaigns = data || [];
        renderCampaigns();
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Función para obtener el color del badge según el estado
function getStatusBadge(status) {
    const statusMap = {
        active: { class: "bg-success", text: "Active" },
        completed: { class: "bg-primary", text: "Completed" },
        paused: { class: "bg-warning", text: "Paused" },
        draft: { class: "bg-secondary", text: "Draft" },
    };
    const statusInfo = statusMap[status] || {
        class: "bg-secondary",
        text: "Without status",
    };
    return `<span class="badge ${statusInfo.class} status-badge">${statusInfo.text}</span>`;
}

// Función para calcular el porcentaje de progreso
function calculateProgress(marked, total) {
    return total > 0 ? Math.round((marked / total) * 100) : 0;
}

// Función para renderizar las campañas
function renderCampaigns() {
    const container = document.getElementById("campaignsContainer");
    container.innerHTML = "";

    campaigns.forEach((campaign) => {
        const progress = calculateProgress(
            campaign.markedContacts,
            campaign.totalContacts
        );
        const cardClass = campaign.isMarking
            ? "campaign-card marking-active"
            : "campaign-card";

        const campaignCard = `
            <div class="col-md-6 col-lg-4 mb-4">
                <form method="POST" id="uploadForm-${campaign.id}" enctype="multipart/form-data">
                    <div class="card ${cardClass}" id="card-${campaign.id}">
                        ${getStatusBadge(campaign.status)}
                        <div class="card-header campaign-header">
                            <h5 class="card-title mb-0">
                                <i class="fas fa-campaign me-2"></i>${campaign.name}
                            </h5>
                        </div>
                        <div class="card-body">
                            <p class="card-text text-muted">${
                                campaign.description
                            }</p>
                            
                            <div class="campaign-stats mb-3">
                                <div class="d-flex justify-content-between">
                                    <span><i class="fas fa-users me-1"></i>Contacts: ${campaign.totalContacts.toLocaleString()}</span>
                                    <span><i class="fas fa-calendar me-1"></i>${new Date(
                                        campaign.createdDate
                                    ).toLocaleDateString()}</span>
                                </div>
                            </div>

                            <div class="progress-section">
                                <div class="progress-info">
                                    <small class="text-muted">Dialing progress</small>
                                    <small class="fw-bold">${campaign.markedContacts.toLocaleString()} / ${campaign.totalContacts.toLocaleString()}</small>
                                </div>
                                <div class="progress mb-2" style="height: 20px;">
                                    <div class="progress-bar progress-bar-gradient" 
                                            style="width: ${progress}%;"
                                            id="progress-${campaign.id}">
                                        <span class="small">${progress}%</span>
                                    </div>
                                </div>
                            </div>

                            <div class="marking-controls" id="controls-${
                                campaign.id
                            }">
                                <div class="d-flex justify-content-between align-items-center mb-3 p-2 bg-light rounded">
                                    <span class="text-success"><i class="fas fa-phone-alt me-2"></i>Marcación en progreso...</span>
                                    <button class="btn btn-sm btn-outline-danger" onclick="stopMarking(${
                                        campaign.id
                                    })">
                                        <i class="fas fa-stop me-1"></i>Detener
                                    </button>
                                </div>
                            </div>

                            <div class="d-grid gap-2 d-md-block">
                                <button class="btn btn-mark btn-custom me-2" onclick="toggleMarking(${
                                    campaign.id
                                })" id="markBtn-${campaign.id}">
                                    <i class="fas fa-phone me-2"></i>Dial
                                </button>
                                <button class="btn btn-view btn-custom me-2" onclick="viewCampaign(${
                                    campaign.id
                                })">
                                    <i class="fas fa-eye me-2"></i>View
                                </button>
                                <button class="btn btn-config btn-custom" onclick="configCampaign(${
                                    campaign.id
                                })">
                                    <i class="fas fa-cog me-2"></i>Config
                                </button>
                            </div>
                            <div class="mt-3">
                                <div class="file-upload-area" onclick="document.getElementById('fileInput-${
                                    campaign.id
                                }').click()" 
                                        ondrop="handleDrop(event, ${campaign.id})" 
                                        ondragover="handleDragOver(event)" 
                                        ondragleave="handleDragLeave(event)">
                                    <i class="fas fa-cloud-upload-alt fa-2x text-muted mb-2"></i>
                                    <p class="mb-1">Upload CSV or Excel</p>
                                    <small class="text-muted">Drag files here or click to select</small>
                                    <input type="file" id="fileInput-${
                                        campaign.id
                                    }" accept=".csv,.xlsx,.xls" 
                                            style="display: none;" onchange="handleFileSelect(event, ${
                                                campaign.id
                                            })">
                                </div>
                            </div>
                        </div>
                    </div>
                </form>
            </div>
        `;

        container.innerHTML += campaignCard;
    });
}

// Función para iniciar/detener marcación
function toggleMarking(campaignId) {
    const campaign = campaigns.find((c) => c.id === campaignId);
    const markBtn = document.getElementById(`markBtn-${campaignId}`);
    const controls = document.getElementById(`controls-${campaignId}`);
    const card = document.getElementById(`card-${campaignId}`);

    if (!campaign.isMarking) {
        campaign.isMarking = true;
        markBtn.innerHTML = '<i class="fas fa-pause me-2"></i>Pausar';
        markBtn.classList.remove("btn-mark");
        markBtn.classList.add("btn-warning");
        controls.style.display = "block";
        card.classList.add("marking-active");

        // Simular progreso de marcación
        simulateMarking(campaignId);
    } else {
        stopMarking(campaignId);
    }
}

// Función para detener marcación
function stopMarking(campaignId) {
    const campaign = campaigns.find((c) => c.id === campaignId);
    const markBtn = document.getElementById(`markBtn-${campaignId}`);
    const controls = document.getElementById(`controls-${campaignId}`);
    const card = document.getElementById(`card-${campaignId}`);

    campaign.isMarking = false;
    markBtn.innerHTML = '<i class="fas fa-phone me-2"></i>Marcar';
    markBtn.classList.remove("btn-warning");
    markBtn.classList.add("btn-mark");
    controls.style.display = "none";
    card.classList.remove("marking-active");

    if (campaign.markingInterval) {
        clearInterval(campaign.markingInterval);
        campaign.markingInterval = null;
    }
}

// Simular progreso de marcación
function simulateMarking(campaignId) {
    const campaign = campaigns.find((c) => c.id === campaignId);

    campaign.markingInterval = setInterval(() => {
        if (
            campaign.markedContacts < campaign.totalContacts &&
            campaign.isMarking
        ) {
            // Incrementar contactos marcados (simulación)
            const increment = Math.min(
                Math.floor(Math.random() * 5) + 1,
                campaign.totalContacts - campaign.markedContacts
            );
            campaign.markedContacts += increment;

            // Actualizar barra de progreso
            const progress = calculateProgress(
                campaign.markedContacts,
                campaign.totalContacts
            );
            const progressBar = document.getElementById(
                `progress-${campaignId}`
            );
            progressBar.style.width = `${progress}%`;
            progressBar.innerHTML = `<span class="small">${progress}%</span>`;

            // Actualizar texto de contactos
            renderCampaigns();
        } else {
            // Completar marcación
            stopMarking(campaignId);
            if (campaign.markedContacts >= campaign.totalContacts) {
                campaign.status = "completed";
                renderCampaigns();
            }
        }
    }, 2000); // Actualizar cada 2 segundos
}

// Función para ver detalles de campaña
function viewCampaign(campaignId) {
    const campaign = campaigns.find((c) => c.id === campaignId);
    const progress = calculateProgress(
        campaign.markedContacts,
        campaign.totalContacts
    );
    const successRate = Math.min(Math.floor(Math.random() * 30) + 70, 100); // Simular tasa de éxito

    // Actualizar contenido del modal
    document.getElementById("modalCampaignName").textContent = campaign.name;
    document.getElementById("modalTotalContacts").textContent =
        campaign.totalContacts.toLocaleString();
    document.getElementById("modalMarkedContacts").textContent =
        campaign.markedContacts.toLocaleString();
    document.getElementById("modalSuccessRate").textContent = `${successRate}%`;
    document.getElementById("modalProgressBar").style.width = `${progress}%`;
    document.getElementById("modalProgressText").textContent = `${progress}%`;

    // Mostrar modal
    const modal = new bootstrap.Modal(document.getElementById("campaignModal"));
    modal.show();
}

function configCampaign(campaignId) {
    getListCampaigns()
    const campaign = campaigns.find((c) => c.id === campaignId);

    // Actualizar contenido del modal
    document.getElementById("modalConfigureCampaignName").textContent = `Configure Campaign: ${campaign.name}`;
    document.getElementById("campaignMaxCurrentCallPerAgent").value = campaign.maxConcurrentCalls;
    document.getElementById("campaignIdConfig").value = campaign.id;

    // Mostrar modal
    showOrHideModal('campaignConfigModal', show=true);
}

function sendConfigCampaign(campaignId, maxConcurrentCallsPerAgent) {
    fetch('/api/dialer/adminDashboard/campaigns/configure/', {
        method: 'POST',
        body: JSON.stringify({
            campaignId: campaignId,
            maxConcurrentCallsPerAgent: maxConcurrentCallsPerAgent
        })
    })
    .then(response => response.json())
    .then(data => {
        showOrHideModal('campaignConfigModal', show=false);
        Swal.fire({
            title: "Campaign Configured",
            text: "Your campaign has been configured successfully!",
            icon: "success"
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Manejo de archivos
function handleFileSelect(event, campaignId) {
    const files = event.target.files;
    if (files.length > 0) {
        uploadFile(files[0], campaignId);
    }
}

function handleDrop(event, campaignId) {
    event.preventDefault();
    event.stopPropagation();
    event.target.classList.remove("dragover");

    const files = event.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0], campaignId);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    event.target.classList.add("dragover");
}

function handleDragLeave(event) {
    event.target.classList.remove("dragover");
}

function uploadFile(file, campaignId) {
    const form = document.getElementById(`uploadForm-${campaignId}`);

    // Eliminar alertas previas
    const existingAlerts = form.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());

    // Validar tipo de archivo
    const validTypes = [".csv", ".xlsx", ".xls"];
    const fileExtension = "." + file.name.split(".").pop().toLowerCase();

    if (!validTypes.includes(fileExtension)) {
        alert("Por favor selecciona un archivo CSV o Excel (.xlsx, .xls)");
        return;
    }

    const fileName = file.name;
    const fileSize = (file.size / 1024).toFixed(2);

    // Mostrar archivo seleccionado con botón submit
    const alertDiv = document.createElement("div");
    alertDiv.className = "alert alert-info alert-dismissible fade show mt-2";
    alertDiv.innerHTML = `
        <i class="fas fa-file me-2"></i>
        "${fileName}" (${fileSize} KB) listo para subir
        <button type="submit" class="btn btn-primary btn-sm ms-2">Subir</button>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    form.appendChild(alertDiv);
}

function createCampaign(form) {
    formData = new FormData(form);
    fetch('/api/dialer/adminDashboard/campaigns/create/', {
    method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        showOrHideModal('createCampaignModal', show=false);
        getListCampaigns(); // Actualizar la lista de campañas
        Swal.fire({
            title: "Campaign Created",
            text: "Your campaign has been created successfully!",
            icon: "success"
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

function showOrHideModal(modalId, show = true) {
    const modal = document.getElementById(modalId);
    
    if (!modal) {
        console.error(`Modal with ID ${modalId} not found.`);
        return;
    }
    
    // Intenta obtener la instancia existente primero
    let bsModal = bootstrap.Modal.getInstance(modal);
    
    // Si no existe instancia, créala
    if (!bsModal) {
        bsModal = new bootstrap.Modal(modal);
    }

    if (show){
        bsModal.show();
    }else{
        bsModal.hide();
    }
}

// Inicializar la aplicación
document.addEventListener("DOMContentLoaded", function () {
    getListCampaigns();

    const formCreateCampaign = document.getElementById('formCreateCampaign');
    formCreateCampaign.addEventListener('submit', function (event) {
        event.preventDefault();
        createCampaign(formCreateCampaign);
    });

    // Delegación de eventos para los formularios de upload
    const campaignsContainer = document.getElementById('campaignsContainer');
    campaignsContainer.addEventListener('submit', function (event) {
        if (event.target.id.startsWith('uploadForm-')) {
            event.preventDefault();
            const campaignId = event.target.id.split('-')[1];
            const fileInput = event.target.querySelector(`#fileInput-${campaignId}`);
            
            const buttonId = event.submitter?.id || '';
            
            if (buttonId.includes('markBtn')) {
                fetch(`/api/dialer/iniciateCalls/${campaignId}/`, {
                })
                .then(response => response.json())
                .then(data => {
                })
                .catch(error => {
                });
            }else if (fileInput.files.length > 0) {
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                formData.append('campaign_id', campaignId);

                fetch('/headerProcessor/', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    showOrHideModal('modalSelectHeaders', true);
                    populateSelects('modalSelectHeaders', data.headers);
                    modifyValueInput('campaignIdFinally', campaignId);
                    addEventListenerById('formSelectHeaders', 'submit', sendExcel, campaignId, 'formSelectHeaders');
                    // Eliminar alertas previas
                    const existingAlerts = event.target.querySelectorAll('.alert');
                    existingAlerts.forEach(alert => alert.remove());                    
                })
                .catch(error => {
                    console.error('Error:', error);
                    // Mostrar mensaje de error
                    const alertDiv = document.createElement("div");
                    alertDiv.className = "alert alert-danger alert-dismissible fade show mt-2";
                    alertDiv.innerHTML = `
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error al subir el archivo
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    `;
                    event.target.appendChild(alertDiv);
                });
            }
        }
    });

    const formConfigCampaign = document.getElementById('formConfigCampaign');
    formConfigCampaign.addEventListener('submit', function (event) {
        event.preventDefault();
        const campaignId = document.getElementById("campaignIdConfig").value
        const maxConcurrentCallsPerAgent = document.getElementById("campaignMaxCurrentCallPerAgent").value
        sendConfigCampaign(campaignId, maxConcurrentCallsPerAgent);
    });
});

function modifyValueInput(inputId, value) {
    const input = document.getElementById(inputId);
    if (input) {
        input.value = value;
    } else {
        console.error(`Input with ID ${inputId} not found.`);
    }
}

function sendExcel(campaignId, formId) {
    const form = document.getElementById(formId);
    const inputFile = document.getElementById(`fileInput-${campaignId}`);
    const formData = new FormData(form);
    formData.append('inputFile', inputFile.files[0]);
    formData.append('campaignId', campaignId);

    fetch('/api/dialer/adminDashboard/campaigns/processExcelForDialer/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        Swal.fire({
            title: "Excel Sent",
            text: "Your Excel file has been sent successfully!",
            icon: "success"
        }).then(() => {
            const tableContainer = document.getElementById(`tableContainer`);
            tableContainer.innerHTML = generateHtmlTable(data.errors);
            showOrHideModal('modalSelectHeaders', show=false)
            showOrHideModal('modalTable', show=true)
            getListCampaigns()
        });
    })
    .catch(error => {
        console.error('Error:', error);
        Swal.fire({
            title: "Error",
            text: "There was an error sending the Excel file.",
            icon: "error"
        });
    });
}

function generateHtmlTable(data) {
  if (!Array.isArray(data) || data.length === 0) {
    return '<p>No data available.</p>';
  }

  // Extract table headers from keys of the first object
  const headers = Object.keys(data[0]);

  // Start building HTML table
  let html = `<table id="table" border="1" cellspacing="0" cellpadding="5" class="table table-striped table-bordered">`;
  
  // Create header row
  html += '<thead><tr>';
  headers.forEach(header => {
    html += `<th>${header}</th>`;
  });
  html += '</tr></thead>';

  // Create data rows
  html += '<tbody>';
  data.forEach(row => {
    html += '<tr>';
    headers.forEach(header => {
        html += `<td>${row[header] !== null ? row[header] : ''}</td>`;
    });
    html += '</tr>';
  });
  html += '</tbody>';

  html += '</table>';

  return html;
}

function addEventListenerById(elementId, eventName, handler, ...args) {
    const element = document.getElementById(elementId);
    if (element) {
        element.addEventListener(eventName, (e) => {
            e.preventDefault();
            handler(...args);
        });
    } else {
        console.error(`Element with ID ${elementId} not found.`);
    }
}

function populateSelects(divId, options) {
  const selects = getSelects(divId);
  
  if (selects.length === 0) {
    console.error('No se encontraron selects en el div especificado');
    return;
  }

  selects.forEach(select => {
    // Limpiamos las opciones existentes
    select.innerHTML = '';
    
    // Agregamos la opción por defecto
    const defaultOption = document.createElement('option');
    defaultOption.disabled = true;
    defaultOption.selected = true;
    defaultOption.textContent = 'Select one';
    select.appendChild(defaultOption);
    
    // Agregamos las nuevas opciones
    options.forEach(optionText => {
      const optionElement = document.createElement('option');
      optionElement.value = optionText; // Usamos el texto como valor
      optionElement.textContent = optionText;
      select.appendChild(optionElement);
    });
  });
}

function getSelects(divId) {
  const contenedor = document.getElementById(divId);
  if (!contenedor) {
    console.error('No se encontró el div con el ID especificado');
    return [];
  }
  return Array.from(contenedor.getElementsByTagName('select'));
}