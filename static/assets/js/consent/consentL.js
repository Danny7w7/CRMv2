// Variables globales
let canvas, ctx, isDrawing = false;

// Inicializar cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    initSignaturePad();
    initFormEvents();
    updateDynamicText();
    initFileUpload();
    initAdditionalCoverageToggle(); // Nueva función para manejar cobertura adicional
});

// Nueva función para manejar la visibilidad de cobertura adicional
function initAdditionalCoverageToggle() {
    const ncaSelect = document.getElementById('nca');
    const additionalCoverageDiv = document.querySelector('.coberturaA').closest('.row');
    const needsDescriptionDiv = document.querySelector('.necesidadesCobertura').closest('.row');
    
    // Ocultar los divs inicialmente
    if (additionalCoverageDiv) {
        additionalCoverageDiv.style.display = 'none';
    }
    if (needsDescriptionDiv) {
        needsDescriptionDiv.style.display = 'none';
    }
    
    // Agregar event listener al select
    if (ncaSelect) {
        ncaSelect.addEventListener('change', function() {
            const showDivs = this.value === 'True';
            
            if (additionalCoverageDiv) {
                additionalCoverageDiv.style.display = showDivs ? 'block' : 'none';
            }
            if (needsDescriptionDiv) {
                needsDescriptionDiv.style.display = showDivs ? 'block' : 'none';
            }
            
            // Si se ocultan los divs, limpiar las selecciones
            if (!showDivs) {
                // Desmarcar todos los checkboxes de cobertura adicional
                const coverageCheckboxes = document.querySelectorAll('.bg-lila input[type="checkbox"]');
                coverageCheckboxes.forEach(checkbox => {
                    checkbox.checked = false;
                });
                
                // Limpiar el textarea de necesidades
                const needsTextarea = document.getElementById('inputApplicants');
                if (needsTextarea) {
                    needsTextarea.value = '';
                }
            }
        });
    }
}

// Inicializar pad de firma
function initSignaturePad() {
    canvas = document.getElementById('drawingCanvas');
    ctx = canvas.getContext('2d');
    
    // Configurar el canvas
    canvas.width = 330;
    canvas.height = 150;
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';

    // Eventos de mouse
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);
    canvas.addEventListener('mouseout', stopDrawing);

    // Eventos táctiles
    canvas.addEventListener('touchstart', handleTouch);
    canvas.addEventListener('touchmove', handleTouch);
    canvas.addEventListener('touchend', stopDrawing);

    // Botón limpiar
    document.getElementById('clearCanvas').addEventListener('click', clearCanvas);
}

function startDrawing(e) {
    isDrawing = true;
    const rect = canvas.getBoundingClientRect();
    ctx.beginPath();
    ctx.moveTo(e.clientX - rect.left, e.clientY - rect.top);
}

function draw(e) {
    if (!isDrawing) return;
    const rect = canvas.getBoundingClientRect();
    ctx.lineTo(e.clientX - rect.left, e.clientY - rect.top);
    ctx.stroke();
}

function stopDrawing() {
    isDrawing = false;
}

function handleTouch(e) {
    e.preventDefault();
    const touch = e.touches[0];
    const mouseEvent = new MouseEvent(e.type === 'touchstart' ? 'mousedown' : 
                                    e.type === 'touchmove' ? 'mousemove' : 'mouseup', {
        clientX: touch.clientX,
        clientY: touch.clientY
    });
    canvas.dispatchEvent(mouseEvent);
}

function clearCanvas() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// Actualizar texto dinámico en tiempo real
function updateDynamicText() {
    const firstName = document.getElementById('inputName').value || '[Nombre]';
    const lastName = document.getElementById('inputLastName').value || '[Apellido]';
    const agent = document.getElementById('selectAgent').value !== 'no_valid' ? 
                document.getElementById('selectAgent').value : '[Agente]';
    
    const fullName = `${firstName} ${lastName}`;
    
    // Actualizar todos los spans dinámicos
    document.getElementById('textName').textContent = fullName;
    document.getElementById('textName2').textContent = fullName;
    document.getElementById('textName3').textContent = fullName;
    document.getElementById('textAgent').textContent = agent;
    document.getElementById('textAgent2').textContent = agent;
    document.getElementById('textAgent3').textContent = agent;
}

// Inicializar eventos del formulario
function initFormEvents() {
    // Actualizar texto dinámico cuando cambien los campos
    document.getElementById('inputName').addEventListener('input', updateDynamicText);
    document.getElementById('inputLastName').addEventListener('input', updateDynamicText);
    document.getElementById('selectAgent').addEventListener('change', updateDynamicText);

    // Evento principal del formulario
    document.getElementById('submitButton').addEventListener('click', handleSubmit);

    // Validación de teléfono
    document.getElementById('inputPhone').addEventListener('input', validatePhone);
    
    // Validación de email
    document.getElementById('inputEmail').addEventListener('input', validateEmail);
}

// Manejar el envío del formulario
async function handleSubmit(e) {
    e.preventDefault();
    
    if (!validateForm()) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Por favor complete todos los campos requeridos correctamente.'
        });
        return;
    }

    try {
        // Mostrar loading
        Swal.fire({
            title: 'Procesando...',
            text: 'Generando PDF y enviando por correo. Esto puede tomar unos momentos...',
            allowOutsideClick: false,
            showConfirmButton: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        // Generar PDF
        const pdfBlob = await generatePDFBlob();
        
        // Enviar por correo
        const result = await sendPDFByEmail(pdfBlob);

        Swal.fire({
            icon: 'success',
            title: '¡Éxito!',
            text: 'El formulario ha sido enviado correctamente por correo electrónico.',
            showConfirmButton: true
        });

    } catch (error) {
        
        let errorMessage = 'Hubo un problema al procesar el formulario.';
        
        if (error.message.includes('Timeout') || error.message.includes('timeout')) {
            errorMessage = 'La operación tardó demasiado tiempo. Verifique la configuración del servidor de correo.';
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: `${errorMessage} Por favor intente nuevamente.`,
            showConfirmButton: true
        });
    }
}

// Generar PDF y devolver como Blob
async function generatePDFBlob() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    
    // Configurar fuente
    doc.setFont('helvetica');
    
    let yPosition = 20;
    const lineHeight = 6;
    const margin = 20;
    const pageWidth = doc.internal.pageSize.width;
    const maxWidth = pageWidth - (margin * 2);

    // Título
    doc.setFontSize(16);
    doc.setFont('helvetica', 'bold');
    doc.text('AGENTE EN REGISTRO', pageWidth / 2, yPosition, { align: 'center' });
    yPosition += 10;
    
    doc.setFontSize(12);
    doc.text('AUTORIZACIÓN DE ENTREGA INFORMACIÓN PARA ENROLAMIENTO EN EL MERCADO DE SALUD', 
            pageWidth / 2, yPosition, { align: 'center' });
    yPosition += 15;

    // Función para añadir texto con salto de línea
    function addText(text, fontSize = 10, isBold = false) {
        doc.setFontSize(fontSize);
        doc.setFont('helvetica', isBold ? 'bold' : 'normal');
        
        const lines = doc.splitTextToSize(text, maxWidth);
        lines.forEach(line => {
            if (yPosition > 280) {
                doc.addPage();
                yPosition = 20;
            }
            doc.text(line, margin, yPosition);
            yPosition += lineHeight;
        });
        yPosition += 2;
    }

    // Obtener datos del formulario
    const formData = getFormData();
    
    // Información personal
    addText('INFORMACIÓN PERSONAL', 12, true);
    addText(`Nombre: ${formData.firstName} ${formData.lastName}`);
    addText(`Teléfono: ${formData.phone}`);
    addText(`Email: ${formData.email}`);
    addText(`Fecha de Nacimiento: ${formData.dateBirth}`);
    addText(`Dirección: ${formData.address}`);
    if (formData.apto) addText(`Apartamento: ${formData.apto}`);
    addText(`Ciudad: ${formData.city}, Estado: ${formData.state}, ZIP: ${formData.zipcode}`);
    yPosition += 5;

    // Información adicional
    addText('INFORMACIÓN ADICIONAL', 12, true);
    addText(`Aplica: ${formData.apply}`);
    addText(`Ingreso Anual: $${formData.taxes}`);
    addText(`Tipo de Ingreso: ${formData.work}`);
    addText(`Estatus Migratorio: ${formData.migrationStatus}`);
    addText(`Social Security: ${formData.ssn || 'No proporcionado'}`);
    addText(`Agente: ${formData.agent}`);
    yPosition += 5;

    // Métodos de contacto
    addText('MÉTODOS DE CONTACTO AUTORIZADOS', 12, true);
    const contactMethods = [];
    if (formData.contactPhone) contactMethods.push('Teléfono');
    if (formData.contactSMS) contactMethods.push('SMS');
    if (formData.contactEmail) contactMethods.push('Email');
    if (formData.contactWhatsapp) contactMethods.push('WhatsApp');
    addText(`Autoriza contacto por: ${contactMethods.join(', ')}`);
    yPosition += 5;

    // Consentimiento de mensajes de texto
    addText('CONSENTIMIENTO DE MENSAJES DE TEXTO', 12, true);
    addText(`Acepta recibir mensajes de texto automatizados de Lapeira & Associates LLC: ${formData.consentAccepted ? 'SÍ' : 'NO'}`);
    if (formData.consentAccepted) {
        addText('Al suministrar su número de teléfono, usted está de acuerdo en recibir mensajes de texto automatizados de Lapeira & Associates LLC con información respecto a opciones de seguro médico, beneficios, productos de seguros, actualizaciones de pólizas, primas, solicitudes y asuntos relacionados para ayudarme o recordarme de cualquier acción necesaria para mantener mi póliza al día. Usted está de acuerdo con nuestros Términos de Uso Terms of Use y nuestra Política de Privacidad. Su autorización no es condición para compra. Responda HELP para ayuda. Rates de msg & data pueden aplicar. Hasta 5 msgs/mes. Responda STOP para opt-out en cualquier momento.');
    }
    yPosition += 5;

    // Cobertura adicional (nueva sección)
    addText('COBERTURA ADICIONAL', 12, true);
    addText(`Necesita cobertura adicional: ${formData.needsAdditionalCoverage ? 'SÍ' : 'NO'}`);
    
    if (formData.needsAdditionalCoverage && formData.additionalCoverageTypes.length > 0) {
        addText(`Tipos de cobertura solicitados: ${formData.additionalCoverageTypes.join(', ')}`);
    }
    
    if (formData.coverageNeeds) {
        addText(`Descripción de necesidades: ${formData.coverageNeeds}`);
    }
    yPosition += 5;

    // Aplicantes adicionales
    if (formData.additionalApplicants) {
        addText('APLICANTES ADICIONALES', 12, true);
        addText(formData.additionalApplicants);
        yPosition += 5;
    }

    // Derechos y autorización (texto completo)
    addText('MIS DERECHOS COMO PACIENTE', 12, true);
    
    // Párrafo 1
    addText(`Yo, ${formData.firstName} ${formData.lastName}, autorizo a ${formData.agent} de Lapeira & Associates LLC para servir como mi agente y broker de seguros de salud, es decir mi Agente de Registro, para mi y las personas en mi núcleo familiar, cuando aplica, para el propósito de enrolamiento en un Plan Médico Calificado ofrecido en el Mercado de Salud Federal.`);
    
    // Párrafo 2
    addText(`Al firmar esta forma, autorizo a ${formData.agent}, y su staff, a trabajar para mi y las personas en mi núcleo familiar, cuando aplica, en las siguientes funciones de apoyo de seguro y cualquier otra tarea administrativa necesaria para mantener mi solicitud y cobertura en buen estado, como sigue:`);
    
    // Lista numerada
    addText('1. Realizar búsquedas de aplicaciones nuevas o actuales en el mercado de salud.');
    addText('2. Completar una aplicación para búsqueda de eligibilidad y enrolamiento en el Mercado de Salud Federal, o en programas de gobierno tales como Medicaid y CHIP, en los sitios de Enrolamiento Directo del Mercado de Salud, o enrolamiento en programas del mercado de salud que ayudan a aplicar a crédito fiscales o enrolamiento de productos de seguros en planes a nivel estatal.');
    addText('3. Proveer mantenimiento de mi cuenta en el Mercado de Salud Federal, asistencia en enrolamiento, información sobre los beneficios de los planes, nuevos productos, beneficios de nuevos productos, y asesoría en los pagos de transacciones si es necesario.');
    addText('4. Apoyar si es necesario en responder inquietudes del Mercado de Salud Federal en lo referente a mi aplicación.');
    addText(`5. Consentimiento de comunicación (Cumplimiento TCPA): Yo, ${formData.firstName} ${formData.lastName}, doy mi consentimiento para recibir comunicaciones de Lapeira & Associates LLC con respecto a opciones de seguro de salud, beneficios, productos de seguros, actualizaciones de pólizas, primas, solicitudes y asuntos relacionados a través de llamadas telefónicas, correos electrónicos, mensajes SMS y otras formas de comunicación para ayudarme o recordarme cualquier acción necesaria para mantener mi póliza en buen estado. Entiendo que dichas comunicaciones pueden involucrar el uso de sistemas automatizados o mensajes de voz pregrabados de Lapeira & Associates LLC en el número proporcionado. Al proporcionar mi información de contacto con mi firma electrónica, cuando hago clic en el botón "enviar", acepto los Términos de Uso de Lapeira & Associates LLC. Este consentimiento incluye aceptar resolver cualquier reclamo de la Ley de Protección al Consumidor de Teléfonos mediante arbitraje. Esto aplica incluso si su número está en una lista de no llamar. Aceptar estas llamadas o textos no es un requisito para comprar bienes o servicios de nosotros. Al recibir un mensaje de texto, puede responder SI para recibir actualizaciones e información sobre su póliza de Lapeira & Associates LLC También puede responder AYUDA para obtener ayuda. Pueden aplicarse tarifas de mensajes y datos. Hasta 5 mensajes/mes. Responda ALTO para cancelar en cualquier momento. Para obtener más información sobre nuestras Políticas de Privacidad, haga clic aquí: https://lapeirainsurance.com/privacy-policy/. Para obtener más información sobre nuestros Términos de Uso, haga clic aquí: https://lapeirainsurance.com/terms-of-use/.`);
    
    yPosition += 3;
    
    // Párrafos adicionales
    addText('Entiendo que mi Agente de Registro no utilizará o compartirá mi información de identificación personal (PII) para ningún propósito excepto los aquí listados en esta autorización. Entiendo que esta autorización será válida hasta que sea revocada por mi en cualquier momento. Para revocar esta autorización, debo hacerlo por escrito y enviarlo a la persona correspondiente a través del correo electrónico: client@lapeira.com.');
    
    addText('Entiendo que la información que yo le suministre a mi Agente de Registro se va a utilizar ÚNICAMENTE para asistirme en verificar mi elegibilidad y mi aplicacion o enrolamiento en el mercado de salud federal (Marketplace). Esta aprobación incluye la búsqueda de una aplicacion activa utilizando la páginas web aprobadas para el enrolamiento clásico directo (DE) o el Enhanced Direct Enrollment (EDE). Así mismo, entiendo que no tengo que compatir otra informacion adicional excepto la que es requerida para mi enrolamiento o verificacion de eligibilidad en el mercado de salud federal (Marketplace)');
    
    yPosition += 3;
    
    // Reconocimiento de Información Correcta
    addText('RECONOCIMIENTO DE INFORMACIÓN CORRECTA Y NO FALSIFICACIÓN', 11, true);
    addText('Al firmar este formulario, afirmo y reconozco que he sido completamente informado y se me ha brindado una explicación clara sobre lo siguiente:');
    addText('1. Los beneficios específicos incluidos en el plan de salud, incluyendo cualquier cobertura de seguro o beneficios asociados.');
    addText('2. Si el plan de salud en el que me estoy inscribiendo es considerado un plan de salud mayor o integral, o si es equivalente a dicha cobertura de seguro.');
    addText('3. Los costos verdaderos y precisos asociados con el plan de salud, incluyendo primas, deducibles y otras obligaciones financieras.');
    
    addText('Además, confirmo que no se me ha ofrecido ni prometido ningún tipo de ofertas gratuitas, recompensas en efectivo, reembolsos u otros incentivos relacionados con la inscripción en el plan de salud. Reconozco que no se me ha hecho ninguna afirmación o promesa sobre este tipo de incentivos durante el proceso de inscripción.');
    
    yPosition += 3;
    
    // Certificación de Revisión
    addText('CERTIFICACIÓN DE REVISIÓN Y RECONOCIMIENTO DE LA INFORMACIÓN', 11, true);
    addText(`Yo, ${formData.firstName} ${formData.lastName}, he revisado y confirmado que la información para mi aplicación en el mercado de salud es CORRECTA Y VERIDICA y estará disponible como es requerido por el Centro de Servicios de Medicare & Medicaid (CMS) para efectos de elegibilidad y enrolamiento.`);
    
    addText(`Nombre del Agente en Registro: ${formData.agent}`);
    addText('Nombre de la Agencia en Registro: Lapeira & Associates LLC');
    addText('Teléfono de la Agencia: +1 (855) 963 6900');
    
    yPosition += 5;

    // Firma
    if (canvas && !isCanvasEmpty()) {
        addText('FIRMA DIGITAL', 12, true);
        const signatureData = canvas.toDataURL('image/png');
        doc.addImage(signatureData, 'PNG', margin, yPosition, 80, 30);
        yPosition += 35;
    }

    addText(`Fecha: ${new Date().toLocaleDateString()}`);
    addText(`Firmado por: ${formData.firstName} ${formData.lastName}`);

    return doc.output('blob');
}

// Enviar PDF por correo
async function sendPDFByEmail(pdfBlob) {
    const formData = new FormData();
    const userData = getFormData();
    
    // Agregar el PDF
    formData.append('pdf_file', pdfBlob, `Consentimiento_${userData.firstName}_${userData.lastName}.pdf`);
    
    // Agregar datos del formulario
    formData.append('first_name', userData.firstName);
    formData.append('last_name', userData.lastName);
    formData.append('phone', userData.phone);
    formData.append('agent', userData.agent);

    try {
        
        // Crear un controller para poder cancelar la petición si es necesario
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 60000); // 60 segundos timeout
        
        // Enviar a Django backend
        const response = await fetch('/sendConsentForm/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            signal: controller.signal
        });

        clearTimeout(timeoutId);        

        if (!response.ok) {
            const errorData = await response.json().catch(() => null);
            const errorMessage = errorData?.error || `Error HTTP: ${response.status}`;
            throw new Error(errorMessage);
        }

        const result = await response.json();
        return result;

    } catch (error) {
        if (error.name === 'AbortError') {
            throw new Error('La operación tardó demasiado tiempo. Verifique su conexión a internet.');
        }
        throw error;
    }
}

// Función mejorada para manejar el envío del formulario
async function handleSubmit(e) {
    e.preventDefault();
    
    if (!validateForm()) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: 'Por favor complete todos los campos requeridos correctamente.'
        });
        return;
    }

    try {
        // Mostrar loading
        Swal.fire({
            title: 'Procesando...',
            text: 'Generando PDF y enviando por correo',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        // Generar PDF
        const pdfBlob = await generatePDFBlob();
        
        // Enviar por correo
        const result = await sendPDFByEmail(pdfBlob);

        Swal.fire({
            icon: 'success',
            title: 'Formulario enviado correctamente',
            text: 'Gracias por enviar el consentimiento.',
            timer: 5000,
            timerProgressBar: true,
            confirmButtonText: 'OK',
            allowOutsideClick: false,
            allowEscapeKey: false,
            willClose: () => {
                // Esto se ejecuta si el usuario no hace clic y se cierra por el temporizador
                location.reload();
            }
        }).then((result) => {
            if (result.isConfirmed) {
                // Esto se ejecuta si el usuario hace clic en "OK"
                location.reload();
            }
        });

    } catch (error) {
        Swal.fire({
            icon: 'error',
            title: 'Error',
            text: `Hubo un problema al procesar el formulario: ${error.message}. Por favor intente nuevamente.`
        });
    }
}

// Función mejorada para obtener el token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    
    // Si no encuentra el token, intentar obtenerlo del meta tag
    if (!cookieValue) {
        const metaTag = document.querySelector('[name=csrf-token]');
        if (metaTag) {
            cookieValue = metaTag.getAttribute('content');
        }
    }
    return cookieValue;
}

// Obtener datos del formulario (modificada para incluir cobertura adicional)
function getFormData() {
    // Obtener tipos de cobertura adicional seleccionados
    const additionalCoverageTypes = [];
    const coverageCheckboxes = document.querySelectorAll('.bg-lila input[type="checkbox"]:checked');
    coverageCheckboxes.forEach(checkbox => {
        additionalCoverageTypes.push(checkbox.name);
    });

    return {
        firstName: document.getElementById('inputName').value,
        lastName: document.getElementById('inputLastName').value,
        phone: document.getElementById('inputPhone').value,
        email: document.getElementById('inputEmail').value,
        dateBirth: document.getElementById('inputDateBirth').value,
        address: document.getElementById('inputAddress').value,
        apto: document.getElementById('inputApto').value,
        city: document.getElementById('inputCity').value,
        state: document.getElementById('inputState').value,
        zipcode: document.getElementById('inputZipcode').value,
        apply: document.getElementById('apply').value,
        taxes: document.getElementById('inputTaxes').value,
        work: document.getElementById('work').value,
        migrationStatus: document.getElementById('migration_status').value,
        ssn: document.getElementById('inputSSN').value,
        agent: document.getElementById('selectAgent').value,
        additionalApplicants: document.getElementById('inputApplicants').value,
        contactPhone: document.getElementById('Telefono').checked,
        contactSMS: document.getElementById('Sms').checked,
        contactEmail: document.getElementById('Emails').checked,
        contactWhatsapp: document.getElementById('Whatsapp').checked,
        // Nuevos campos para cobertura adicional
        needsAdditionalCoverage: document.getElementById('nca').value === 'True',
        additionalCoverageTypes: additionalCoverageTypes,
        coverageNeeds: document.getElementById('inputApplicants') ? document.getElementById('inputApplicants').value : '',
        // Consentimiento de mensajes de texto
        consentAccepted: document.getElementById('consentChek').checked
    };
}

// Validar formulario
function validateForm() {
    const requiredFields = [
        'inputName', 'inputLastName', 'inputPhone', 'inputDateBirth',
        'inputTaxes', 'selectAgent', 'nca'
    ];

    for (let fieldId of requiredFields) {
        const field = document.getElementById(fieldId);
        if (!field.value || field.value === 'no_valid') {
            field.focus();
            return false;
        }
    }

    // Validar consentimiento de mensajes de texto
    const consentCheckbox = document.getElementById('consentChek');
    if (!consentCheckbox.checked) {
        Swal.fire({
            icon: 'warning',
            title: 'Consentimiento requerido',
            text: 'Debe aceptar el consentimiento de mensajes de texto para continuar.'
        });
        consentCheckbox.focus();
        return false;
    }

    // Validar que al menos un método de contacto esté seleccionado
    const contactMethods = document.querySelectorAll('.contactMethod');
    const hasContactMethod = Array.from(contactMethods).some(method => method.checked);
    
    if (!hasContactMethod) {
        Swal.fire({
            icon: 'warning',
            title: 'Método de contacto requerido',
            text: 'Por favor seleccione al menos un método de contacto.'
        });
        return false;
    }

    // Validar firma
    if (isCanvasEmpty()) {
        Swal.fire({
            icon: 'warning',
            title: 'Firma requerida',
            text: 'Por favor proporcione su firma digital.'
        });
        return false;
    }

    return true;
}

// Verificar si el canvas está vacío
function isCanvasEmpty() {
    const blank = document.createElement('canvas');
    blank.width = canvas.width;
    blank.height = canvas.height;
    return canvas.toDataURL() === blank.toDataURL();
}

// Validaciones
function validatePhone() {
    const phone = document.getElementById('inputPhone').value;
    const error = document.getElementById('error');
    
    if (phone && (phone.length < 10 || phone.length > 11)) {
        error.style.display = 'block';
        return false;
    } else {
        error.style.display = 'none';
        return true;
    }
}

function validateEmail() {
    const email = document.getElementById('inputEmail').value;
    const error = document.getElementById('errorEmail');
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    
    if (email && !emailRegex.test(email)) {
        error.style.display = 'block';
        return false;
    } else {
        error.style.display = 'none';
        return true;
    }
}

// Obtener cookie CSRF para Django
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Inicializar manejo de archivos
function initFileUpload() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('fileInput');
    const fileList = document.getElementById('fileList');

    // Prevenir comportamiento por defecto
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Destacar dropzone cuando se arrastra sobre él
    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, unhighlight, false);
    });

    // Manejar archivos soltados
    dropzone.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight() {
        dropzone.classList.add('bg-primary', 'bg-opacity-10');
    }

    function unhighlight() {
        dropzone.classList.remove('bg-primary', 'bg-opacity-10');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        fileList.innerHTML = '';
        Array.from(files).forEach(file => {
            const li = document.createElement('li');
            li.className = 'list-group-item d-flex justify-content-between align-items-center';
            li.innerHTML = `
                <span>
                    <i class="bi bi-file-earmark"></i>
                    ${file.name} (${(file.size / 1024).toFixed(1)} KB)
                </span>
                <button type="button" class="btn btn-sm btn-outline-danger" onclick="this.parentElement.remove()">
                    <i class="bi bi-trash"></i>
                </button>
            `;
            fileList.appendChild(li);
        });
    }
}