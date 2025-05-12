buttons = document.getElementsByClassName('reportingType');

buttons.forEach(button => {
  button.addEventListener("click", () => changeInputValue('reportingType', button.id));
  button.addEventListener("click", () => changeInputValueWithName('reportingTypeFinally', button.id));
});

function changeInputValue(id, value) {
  document.getElementById(id).value = value
  document.getElementById('buttonSubmit').disabled = false
}

function changeInputValueWithName(name, value) {
  document.getElementsByName(name).forEach(input => {
    input.value = value;
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

function setupFormSendHeaderListener(formId) {
  const formSendHeader = document.getElementById(formId);
  formSendHeader.addEventListener('submit', async function (event) {
    event.preventDefault();

    // Mostrar Sweet Alert de carga
    Swal.fire({
      title: 'Procesando archivo',
      text: 'Por favor espere...',
      allowOutsideClick: false,
      allowEscapeKey: false,
      didOpen: () => {
        Swal.showLoading();
      }
    });

    const fileInput = document.getElementById('file');
    if (!formSendHeader.contains(fileInput)) {
      formSendHeader.appendChild(fileInput);
    }
    const formData = new FormData(formSendHeader);

    try {
      const response = await fetch('/processExcel/', {
        method: 'POST',
        body: formData,
      });

      // Cerrar el Sweet Alert de carga
      Swal.close();
  
      if (response.ok) {
        const data = await response.json()
        console.log(data);
        Swal.fire({
          icon: 'success',
          title: 'Éxito',
          text: 'Archivo procesado correctamente'
        }).then(() => {
          const tableContainer = document.getElementById(`tableContainer`);
          tableContainer.innerHTML = generateHtmlTable(data.unmatchedRecords, data.modalId);
          showModal(`modalTable`);
          downloadTableAsExcel(`table`);
        });
      } else {
        Swal.fire({
          icon: 'error',
          title: 'Error',
          text: 'Error al procesar el archivo'
        });
      }
    } catch (error) {
      Swal.fire({
        icon: 'error',
        title: 'Error',
        text: 'Error en la petición: ' + error.message
      });
    }
  });
}

document.getElementById('uploadForm').addEventListener('submit', async (event) => {
  event.preventDefault(); // prevenir recarga

  const form = event.target;
  const formData = new FormData(form);
  console.log(form)
  console.log(formData)

  const response = await fetch('/headerProcessor/', {
    method: 'POST',
    body: formData
  });

  const data = await response.json();
  console.log(data);
  populateSelects(`${data.modalId}SelectHeader`, data.headers);
  showModal(`modal${data.modalId}`); // Pasamos el ID dinámicamente
  setupFormSendHeaderListener(`${data.modalId}Form`);
});

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

const showModal = (modalId) => {
  try {
    const modalElement = document.getElementById(modalId);
    if (!modalElement) {
      console.error(`No se encontró el modal con ID: ${modalId}`);
      return;
    }
    
    // Creamos una nueva instancia del modal y la almacenamos
    const modalInstance = new bootstrap.Modal(modalElement);
    
    // Mostramos el modal usando la instancia creada
    modalInstance.show();
    
  } catch (error) {
    console.error('Error al mostrar el modal:', error);
  }
};

function downloadTableAsExcel(id) {
  const table = document.getElementById(id);
  const workbook = XLSX.utils.table_to_book(table, { sheet: "Sheet1" });
  XLSX.writeFile(workbook, 'table.xlsx');
}

function generateHtmlTable(data, tableId) {
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

document.addEventListener('DOMContentLoaded', () => {
  const allCheckboxes = document.querySelectorAll('[data-group] input[type="checkbox"]');

  allCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', () => {
      if (checkbox.checked) {
        const group = checkbox.closest('[data-group]');
        const groupCheckboxes = group.querySelectorAll('input[type="checkbox"]');

        groupCheckboxes.forEach(cb => {
          if (cb !== checkbox) {
            cb.checked = false;
          }
        });
      }
    });
  });
});