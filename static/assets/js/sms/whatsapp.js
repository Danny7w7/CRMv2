const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
const url = protocol + window.location.host + '/ws/chatWatsapp/' + chat_id + '/' + company_id + '/';

const buttonSendMessage = document.getElementById('sendMessage');
const inputMessage = document.getElementById('messageContent');
const boxMessage = document.getElementById('chat-content');

if (chat_id != ''){
    const chatRoomName = `whatsapp_${chat_id}_empresa_${company_id}`;
    //console.log('📡 Conectando al canal:', chatRoomName);
    var chatSocket = new WebSocket(url);

    chatSocket.onopen = function (e) {
       // console.log('✅ WebSocket abierto correctamente en URL:', url);
    };

    chatSocket.onclose = function (e) {
       // console.log('❌ WebSocket cerrado');
    };

    chatSocket.onmessage = function (data) {
        const datamsj = JSON.parse(data.data);
        var msj = datamsj.mensaje;
        var type = datamsj.tipo;
        var url = datamsj.url
        var sender = datamsj.sender        
    
        // Validación para asegurar que data.usuario esté definido
        var nombreUsuario = data.usuario ? data.usuario.replace("whatsapp:", "") : "Desconocido";  // Usamos "Desconocido" como valor por defecto
        
        if (sender === 'client'){
            if (type === 'media') {            
                addMessage(msj, 'Client', type, url);
            } else {            
                addMessage(msj, 'Client', type);
            }
        }
        

        if (inputMessage.disabled) {
            activateTextArea(msj)
        } 

    };
    inputMessage.style.height = '40px'
    buttonSendMessage.addEventListener('click', sendMessage);
    inputMessage.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            this.style.height = '40px'; // Ajusta la altura a 2 líneas
            sendMessage();
            e.preventDefault(); // Evita el comportamiento predeterminado del enter
        } else if (e.key === 'Enter' && e.shiftKey) {
            this.style.height = '60px'; // Ajusta la altura a 2 líneas
        }
    });
}

function sendMessage() {
    const message = inputMessage.value.trim();
    if (message) {
        chatSocket.send(JSON.stringify({
            mensaje: message
        }));
        sendFirstMessage(message)
        inputMessage.value = ''; // Limpiar el input después de enviar
    } else {
        //console.log('El mensaje está vacío');
    }
}

function getCurrentTime() {
    const now = new Date();
    let hours = now.getHours();
    const minutes = now.getMinutes().toString().padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12; // Convert to 12-hour format and handle midnight
    return `${hours}:${minutes} ${ampm}`;
}

function addMessage(text, type, typemsj, url=null ,messageTime = getCurrentTime()) {
    if (type == 'Client') {
        const chatContent = document.createElement('div');
        chatContent.classList.add('chat-content-leftside');
    
        const flexContainer = document.createElement('div');
        flexContainer.classList.add('d-flex');
    
        // Create SVG user icon
        const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute('width', '45');
        svg.setAttribute('height', '45');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'none');
        svg.setAttribute('stroke', 'currentColor');
        svg.setAttribute('stroke-width', '2');
        svg.setAttribute('stroke-linecap', 'round');
        svg.setAttribute('stroke-linejoin', 'round');
        svg.classList.add('feather', 'feather-user');
    
        const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
        path.setAttribute('d', 'M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2');
        
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute('cx', '12');
        circle.setAttribute('cy', '7');
        circle.setAttribute('r', '4');
    
        svg.appendChild(path);
        svg.appendChild(circle);
    
        // Create content container
        const contentContainer = document.createElement('div');
        contentContainer.classList.add('flex-grow-1', 'ms-2');
    
        // Create time paragraph
        const timeParagraph = document.createElement('p');
        timeParagraph.classList.add('mb-0', 'chat-time');
        const clientName = chat_name || chat_id;
        timeParagraph.textContent = `${clientName}, ${messageTime}`;
    
        // Create message content
        const messageParagraph = document.createElement('p');
        messageParagraph.classList.add('chat-left-msg');
    
        if (typemsj === 'media') {
            // Validar si el texto (URL de la imagen) está definido y no está vacío
            if (url && url.trim()) {
                const image = document.createElement('img');
                image.src = url;  // Aquí se usa la URL proporcionada por el mensaje
                image.classList.add('img-responsive');
                image.alt = 'Mensaje multimedia';
                messageParagraph.appendChild(image);
            } else {
               // console.log('Error: la URL de la imagen no está disponible o es inválida');
            }
        } else {
            // Si el tipo de mensaje no es MMS, se muestra como texto
            if (text) {
                messageParagraph.innerHTML = text.replace(/\n/g, '<br>');
            } else {
                //console.log('Error: el mensaje de texto está vacío o no está disponible');
            }
        }
        
    
        // Assemble the components
        contentContainer.appendChild(timeParagraph);
        contentContainer.appendChild(messageParagraph);
    
        flexContainer.appendChild(svg);
        flexContainer.appendChild(contentContainer);
    
        chatContent.appendChild(flexContainer);
        boxMessage.appendChild(chatContent);
    } else {
        // User message (right side)
        const chatContent = document.createElement('div');
        chatContent.classList.add('chat-content-rightside');

        const flexContainer = document.createElement('div');
        flexContainer.classList.add('d-flex', 'ms-auto');

        // Create content container
        const contentContainer = document.createElement('div');
        contentContainer.classList.add('flex-grow-1', 'me-2');

        // Create time paragraph
        const timeParagraph = document.createElement('p');
        timeParagraph.classList.add('mb-0', 'chat-time', 'text-end');
        timeParagraph.textContent = `${username}, ${messageTime}`;

        // Create message content
        const messageParagraph = document.createElement('p');
        if (typemsj === 'media') {
            messageParagraph.classList.add('chat-left-msg');
            const image = document.createElement('img');
            image.src = text;
            image.classList.add('img-responsive');
            image.alt = 'Mensaje multimedia';
            messageParagraph.appendChild(image);
        } else {
            messageParagraph.classList.add('chat-right-msg');
            messageParagraph.innerHTML = text.replace(/\n/g, '<br>');
        }

        // Assemble the components
        contentContainer.appendChild(timeParagraph);
        contentContainer.appendChild(messageParagraph);

        flexContainer.appendChild(contentContainer);
        chatContent.appendChild(flexContainer);
        boxMessage.appendChild(chatContent);
    }
    scrollToBottom();
}
function activateTextArea(msg) {    
    // Convertimos el mensaje a mayúsculas para evitar problemas de comparación
    const upperMsg = msg.toUpperCase();

    // Verificamos si el mensaje contiene "YES" o "SI"
    if (upperMsg == "YES" || upperMsg == "SI" || upperMsg == "START") {
        inputMessage.disabled = false; // Habilita el textarea
    }
    if (upperMsg == "STOP") {
        inputMessage.disabled = true; // Habilita el textarea
    }
}

function scrollToBottom() {
    let chatContent = document.getElementById("chat-content");
    chatContent.scrollTop = chatContent.scrollHeight;
}

async function sendFirstMessage(message) {
    const formData = new FormData();
    formData.append('phoneNumber', chat_id);
    formData.append('messageContent', message);

    return fetch('/sendWhatsappConversation/', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server error ${response.status}: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.message === 'No money') {
            return Swal.fire({
                title: "<p style='color: red;'>Insufficient funding</p>",
                text: "Recharge your account, in case of error contact support.",
                icon: "error"
            }).then(() => {
                window.location.reload();
            });
        }
        
        addMessage(message, 'Agent');
        return data;
    })
    .catch((error) => {
       // console.error('Error:', error);
        Swal.fire({
            title: "Error",
            text: `An error occurred while sending the message. Please try again later.<br> Error: ${error.message}`,
            icon: "error"
        });
        throw error;
    });    
}

// Obtener el formulario cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    scrollToBottom()
    const form = document.getElementById('newChat');
    if (form){
        const phoneInput = form.querySelector('input[name="phoneNumber"]');
        form.addEventListener('submit', function(event) {
            // Prevenir el envío por defecto
            event.preventDefault();
            
            // Validar el número de teléfono
            const isValid = validatePhoneNumber(phoneInput.value);
            
            if (isValid) {
                // Si es válido, actualizar el valor del input con el formato correcto
                phoneInput.value = isValid;
                // Enviar el formulario
                form.submit();
            } else {
                // Si no es válido, mostrar un mensaje de error
                alert('Por favor, ingresa un número de teléfono válido de 10 dígitos');
                phoneInput.focus();
            }
        });
    }
    const buttonCreateSecretKey = document.getElementById('buttonCreateSecretKey');
    const buttonSendSecretKey = document.getElementById('buttonSendSecretKey');
    const buttonStartChat = document.getElementById('buttonStartChat');
    
    if (buttonCreateSecretKey) {
        buttonCreateSecretKey.addEventListener('click', () => SecretKey('Create'));
    }
    
    if (buttonSendSecretKey) {
        buttonSendSecretKey.addEventListener('click', () => SecretKey('Send'));
    }

});



function setLanguage(lenguaje) {
    StartChat(lenguaje)
}

function StartChat(lenguaje) {
    const formData = new FormData();
    formData.append('language', lenguaje);

    fetch(`/startChatWhasapp/${chat_id}/`, {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(err => { throw err });
        }
        return response.json();
    })
    .then(data => {
        addMessage(data.message, 'Agent', 'SMS');
        toggleClass('chat-content', 'chat-content-center')
        hideObject('languageDropdown')
    })
    .catch(error => {
        let errorMessage = "Error when trying to create a chat, contact your system administrator.";
        
        if (error.error_detail) {
            errorMessage = `${error.error_title}: ${error.error_detail}`;
        }

        Swal.fire({
            title: "Error",
            text: errorMessage,
            icon: "error"
        });
    });
}

function toggleClass(id, className) {
    const element = document.getElementById(id);
    if (element) {
        element.classList.toggle(className);
    } else {
       // console.error(`Element with id "${id}" not found.`);
    }
}

function hideObject(id) {
    const element = document.getElementById(id);
    if (element) {
        element.style.display = "none";
    } else {
       // console.error(`Element with id "${id}" not found.`);
    }
}

function validatePhoneNumber(phoneNumber) {
    // Eliminar cualquier caracter que no sea número
    const cleanNumber = phoneNumber.toString().replace(/\D/g, '');
    
    // Si el número empieza con 1 y tiene 11 dígitos, es válido
    if (cleanNumber.startsWith('1') && cleanNumber.length === 11) {
        return cleanNumber;
    }
    
    // Si el número tiene exactamente 10 dígitos, agregar 1 al inicio
    if (cleanNumber.length === 10) {
        return '1' + cleanNumber;
    }
    
    // En cualquier otro caso, el número no es válido
    return false;
}

const listChats = document.getElementById('listChats');
if (listChats){
    var anchorsArray = Array.from(listChats.querySelectorAll('a'));
}

const searchInput = document.getElementById('searchInput');
if (searchInput){
    searchInput.addEventListener('input', function() {
        anchorsArray.forEach(anchor => {
            if (isSubsequence(searchInput.value.toLowerCase(), anchor.id.toLowerCase())){
                anchor.style.display = 'block'; 
            }else{
                anchor.style.display = 'none';
            }
        });
    });
}

function isSubsequence(sub, str) {
    let subIndex = 0;

    for (let i = 0; i < str.length; i++) {
        if (str[i] === sub[subIndex]) {
            subIndex++;
        }
        if (subIndex === sub.length) {
            return true;
        }
    }
    return false;
}

function toggleChat() {
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer.classList.contains('show')) {
        chatContainer.classList.remove('show');
        chatContainer.classList.add('hide');
        setTimeout(() => chatContainer.style.display = 'none', 300);
    } else {
        chatContainer.style.display = 'flex';
        chatContainer.classList.remove('hide');
        chatContainer.classList.add('show');
    }
    if (is_message_unread){
        fetch(`/readAllMessages/${chat_id}/${company_id}/`, {
            method: 'POST',
        })
        is_message_unread = false
    }
    scrollToBottom();
}

buttonDarkMode = document.getElementById('dark-mode')
floatingChat = document.getElementById('floating-chat')
buttonDarkMode.addEventListener('click', toggleDarkMode)

function toggleDarkMode() {
    floatingChat.classList.toggle('dark-mode');
}