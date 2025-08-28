// Variables globales
let callStartTime = null;
let callTimer = null;
let isCallActive = false;
let activeCall = null;
let isMuted = false;
let ringtoneAudio = null;
let controlCallId = null;


let stats = {
    totalCalls: 0,
    successCalls: 0,
    avgTime: "0:00",
    conversionRate: 0
};

const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const url = protocol + window.location.host + `/ws/callAlerts/${agent_id}/`;

var callAlertsSocket = new WebSocket(url);

callAlertsSocket.onopen = function (e) {
    console.log('webSocket abierto');
};

callAlertsSocket.onclose = function (e) {
    console.log('webSocket cerrado');
};

callAlertsSocket.onmessage = function (data) {
    const datamsj = JSON.parse(data.data);
    controlCallId = datamsj.callId;
    playRingTone()
    showNotification('Llamada entrante...', 'info');
    updateCustomerInfo(datamsj)
};

// Inicialización
document.addEventListener('DOMContentLoaded', function() {
    updateStats();
});

// Funciones del Timer
function startCallTimer() {
    callStartTime = new Date();
    callTimer = setInterval(updateCallTimer, 1000);
}

function stopCallTimer() {
    if (callTimer) {
        clearInterval(callTimer);
        callTimer = null;
    }
}

function updateCallTimer() {
    if (callStartTime) {
        const now = new Date();
        const elapsed = new Date(now - callStartTime);
        const hours = String(elapsed.getUTCHours()).padStart(2, '0');
        const minutes = String(elapsed.getUTCMinutes()).padStart(2, '0');
        const seconds = String(elapsed.getUTCSeconds()).padStart(2, '0');
        document.getElementById('callTimer').textContent = `${hours}:${minutes}:${seconds}`;
    }
}

// Funciones de Control de Llamadas
function answerCall() {
    if (!isCallActive) {
        isCallActive = true;
        startCallTimer();
        document.getElementById('answerBtn').style.display = 'none';
        document.getElementById('hangupBtn').style.display = 'inline-block';
        showNotification('Llamada contestada', 'success');
    }
}

function hangupCall() {
    if (isCallActive) {
        isCallActive = false;
        isMuted = false;
        stopCallTimer();
        document.getElementById('callTimer').textContent = '00:00:00';
        document.getElementById('answerBtn').style.display = 'inline-block';
        document.getElementById('hangupBtn').style.display = 'none';
        
        // Actualizar estadísticas
        stats.totalCalls++;
        updateStats();
        
        showNotification('Llamada finalizada', 'info');

        showOrHideModal('callOutcome', show=true)
        
        if (activeCall) {
            activeCall.hangup();
        }
    }
}

function muteCall() {
    if (isCallActive) {
        isMuted = !isMuted;
        const muteBtn = document.getElementById('muteBtn');
        const muteIcon = muteBtn.querySelector('i');
        if (isMuted) {
            muteBtn.style.background = '#dc3545';
            muteIcon.className = 'fas fa-microphone-slash';
            activeCall.muteAudio();
            showNotification('Micrófono silenciado', 'warning');
        } else {
            muteBtn.style.background = '#6c757d';
            muteIcon.className = 'fas fa-microphone';
            activeCall.unmuteAudio();
            showNotification('Micrófono activado', 'success');
        }
    }
}

function transferCall() {
    if (isCallActive) {
        const extension = prompt('Ingrese la extensión para transferir:');
        if (extension) {
            fetchData(`/dialer/tranferCallToAgent/`, {
                method: 'POST',
                body: { newAgentId: extension}
            })
            .then(data => {
                hangupCall();
                showNotification('Llamada transferida exitosamente', 'success');
            })
            .catch(err => {
                showNotification(`No se transfirio una monda`, 'info');
            });
        }
    }
}

// Funciones de Utilidad
function saveNotes() {
    const notes = document.getElementById('callNotes').value;
    if (notes.trim()) {
        showNotification('Notas guardadas exitosamente', 'success');
    } else {
        showNotification('Por favor escriba algunas notas antes de guardar', 'warning');
    }
}

function updateStats() {
    fetchData('/dialer/agentDashboard/getStats/')
    .then(data => {
        document.getElementById('totalCalls').textContent = data.callToday;
        document.getElementById('successCalls').textContent = data.callCompleted;
        document.getElementById('avgTime').textContent = data.averageDuration;
        let rate = 0;
        if (data.callToday === 0 && data.callCompleted === 0) {
            rate = 0;
        } else {
            rate = ((data.callCompleted / data.callToday) * 100).toFixed(1);
        }
        stats.conversionRate = rate;
        document.getElementById('conversionRate').textContent = rate + '%';
    })
    .catch(err => console.error(err));

}

function updateCustomerInfo(data) {
    
    document.getElementById('customerName').textContent = data.clientName;
    document.getElementById('customerPhone').textContent = data.clientPhone;
    document.getElementById('customerAddress').textContent = data.clientAddress;
    document.getElementById('customerZipCode').textContent = data.clientZipCode;
    document.getElementById('lastContact').textContent = data.lastCall
    document.getElementById('attempts').textContent = data.attempts
    document.getElementById('customerStatus').textContent = data.status
    document.getElementById('customerStatus').className = 'badge bg-warning';
    document.getElementById('callNotes').value = '';
}

function playRingTone() {
    if (!ringtoneAudio) {
        ringtoneAudio = new Audio(ringtoneStatic); // ajusta la ruta a tu archivo
        ringtoneAudio.loop = true; // se repite en bucle
    }
    ringtoneAudio.play().catch(error => {
        console.error('Error al reproducir el sonido:', error);
    });
}

function stopRingTone() {
    if (ringtoneAudio) {
        ringtoneAudio.pause();
        ringtoneAudio.currentTime = 0; // reinicia el sonido
    }
}

function showNotification(message, type) {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideIn 0.3s ease;
    `;
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Agregar estilos de animación
    const style = document.createElement('style');
    if (!document.querySelector('#notification-styles')) {
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
    }
    
    document.body.appendChild(notification);
    
    // Auto-remove después de 5 segundos
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Funciones del Modal de Estado
function changeStatus() {
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

function updateStatus() {
    const selectedStatus = document.querySelector('input[name="status"]:checked');
    if (selectedStatus) {
        const statusValue = selectedStatus.value;
        const statusText = selectedStatus.nextElementSibling.textContent.trim();

        fetchData(`/dialer/agentDashboard/changeStatus/${agent_id}/`, {
            method: 'POST',
            body: { status: statusValue}
        })
        .then(data => {})
        .catch(err => {});
        
        // Actualizar el indicador visual
        const statusIndicator = document.querySelector('.status-indicator');
        const statusLabel = statusIndicator.nextElementSibling;
        
        statusIndicator.className = `status-indicator status-${statusValue}`;
        statusLabel.textContent = statusText;
        statusLabel.className = `fw-bold text-${getStatusColor(statusValue)}`;
        
        showNotification(`Estado cambiado a: ${statusText}`, 'info');
        
        // Cerrar modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('statusModal'));
        modal.hide();
    }
}

function getStatusColor(status) {
    switch(status) {
        case 'available': return 'success';
        case 'busy': return 'danger';
        case 'break': return 'warning';
        default: return 'secondary';
    }
}

function openScript() {
    showNotification('EN DESARROLLO...', 'info');
    // Aquí podrías mostrar el script de ventas en un modal
}

function logout() {
    if (confirm('¿Está seguro que desea cerrar sesión?')) {
        showNotification('Cerrando sesión...', 'warning');
        // Aquí implementarías la lógica de logout
        setTimeout(() => {
            window.location.href = '/login.html';
        }, 2000);
    }
}

// Atajos de teclado
document.addEventListener('keydown', function(event) {
    // Solo procesar si no estamos escribiendo en un input
    if (event.target.tagName.toLowerCase() === 'input' || 
        event.target.tagName.toLowerCase() === 'textarea') {
        return;
    }
    
    switch(event.key) {
        case 'a':
        case 'A':
            answerCall();
            break;
        case 'h':
        case 'H':
            hangupCall();
            break;
        case 'm':
        case 'M':
            muteCall();
            break;
        case 's':
        case 'S':
            if (event.ctrlKey) {
                event.preventDefault();
                saveNotes();
            }
            break;
    }
});

// Prevenir que la página se cierre accidentalmente durante una llamada
window.addEventListener('beforeunload', function(event) {
    if (isCallActive) {
        event.preventDefault();
        event.returnValue = '¿Está seguro que desea salir? Hay una llamada activa.';
        return event.returnValue;
    }
});

// Función para manejar responsive
function handleResize() {
    if (window.innerWidth < 768) {
        // Ajustar elementos para móvil
        document.querySelectorAll('.control-btn').forEach(btn => {
            btn.style.width = '50px';
            btn.style.height = '50px';
        });
    } else {
        // Restaurar tamaño desktop
        document.querySelectorAll('.control-btn').forEach(btn => {
            btn.style.width = '60px';
            btn.style.height = '60px';
        });
    }
}

window.addEventListener('resize', handleResize);

// Funciones adicionales para mejorar UX
function formatPhoneNumber(phone) {
    // Formatear número telefónico
    return phone.replace(/(\+\d{2})(\d{3})(\d{3})(\d{4})/, '$1 $2 $3 $4');
}

function calculateCallDuration(start, end) {
    const duration = new Date(end - start);
    return `${String(duration.getUTCMinutes()).padStart(2, '0')}:${String(duration.getUTCSeconds()).padStart(2, '0')}`;
}

async function fetchData(url, options = {}) {
    try {
        const response = await fetch(url, {
            method: options.method || 'GET',
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            body: options.body ? JSON.stringify(options.body) : null
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('Fetch error:', error);
        throw error;
    }
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

document.addEventListener("DOMContentLoaded", () => {
    const outcomeCards = document.querySelectorAll(".outcome-card");

    outcomeCards.forEach(card => {
        card.addEventListener("click", () => {
            const isSelected = card.classList.contains("selected");

            // Si ya está seleccionada y vuelven a hacer click -> ejecutar otra función
            if (isSelected) {
                onReselect(card);
            } else {
                // Quitar selección de todas
                outcomeCards.forEach(c => c.classList.remove("selected"));

                // Seleccionar la actual
                card.classList.add("selected");
            }
        });
    });

    function onReselect(card) {
        sendTipification(card.dataset.outcome)
    }
});

function sendTipification(typification) {
    fetchData(`/dialer/agentDashboard/tipification/`, {
        method: 'POST',
        body: { 
            controlCallId: controlCallId,
            agent_id: agent_id,
            typification: typification
        }
    })
    .then(data => {
        hangupCall();
        showNotification('Llamada Tipificada exitosamente', 'success');
        showOrHideModal('callOutcome', show=false)
    })
    .catch(err => {
        showNotification(`No se tipificó la llamada`, 'info');
    });
}

// Autoguardado de notas cada 30 segundos
setInterval(() => {
    const notes = document.getElementById('callNotes').value;
    if (notes.trim() && isCallActive) {
        // Simular autoguardado
        console.log('Autoguardando notas...');
    }
}, 30000);

document.addEventListener('DOMContentLoaded',async  function() {
    
    const client = new TelnyxWebRTC.TelnyxRTC({
        login: sip_username,
        password: sip_password
    });

    client
        .on('telnyx.ready', () => console.log('ready to call'))
        .on('telnyx.notification', (notification) => {
            console.log('notification:', notification)
    });

    client.on('telnyx.notification', (notification) => {
        const call = notification.call;

        if (notification.type === 'callUpdate') {

            if (call.state === 'ringing') {
                call.answer()
            }

            if (call.state === 'active') {
                activeCall = call; // Guardamos la llamada activa
                // Reproducir el audio remoto
                const remoteAudio = document.getElementById('remoteAudio');
                remoteAudio.srcObject = call.remoteStream;
                answerCall()
                stopRingTone()
            }

            if (call.state == 'hangup') {
                hangupCall()
            }
        }
    });


    client.enableMicrophone();
    client.connect();
});