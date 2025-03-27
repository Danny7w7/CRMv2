document.addEventListener("DOMContentLoaded", function () {
    const userRole = document.body.getAttribute("data-user-role");
    const user = document.body.getAttribute("data-username");


    if (!userRole) return;

    const protocol = window.location.protocol === "https:" ? "wss://" : "ws://";
    const socket = new WebSocket(protocol + window.location.host + "/ws/alerts/");

    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        
        if (data.event_type === 'newClient' && !(userRole === "A" || userRole === "AU")) {
            Swal.fire({
                title: data.title,
                text: data.message,
                icon: data.icon,
                confirmButtonText: "Aceptar",
                timer: 5000
            });
        }
        
        else if ( user == data.agent.username && data.event_type === 'newMessage' && !window.location.href.includes("chatSms")) {
            Swal.fire({
                title: data.title,
                text: data.message,
                icon: data.icon,
                showCancelButton: "OK",
                confirmButtonColor: "#19e207",
                cancelButtonColor: "#ea0907",
                confirmButtonText: data.buttonMessage, // Cambiamos el texto del botón
                cancelButtonText:"Ignore"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.open(data.absoluteUrl, '_blank'); // Abre la URL en una nueva pestaña
                }
            });        
        }
        
        else if ( user == data.agent.username  && data.event_type === 'newAccionRequired' ) {
            Swal.fire({
                title: data.title,
                text: data.message,
                icon: data.icon,
                showCancelButton: "OK",
                confirmButtonColor: "#19e207",
                cancelButtonColor: "#ea0907",
                confirmButtonText: data.buttonMessage, // Cambiamos el texto del botón
                cancelButtonText:"Ignore"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.open(data.absoluteUrl, '_blank'); // Abre la URL en una nueva pestaña
                }
            });
        }
        
        else if (userRole === "S" || userRole === "C" || userRole === "Admin" && data.event_type === 'actionCompleted') {
            Swal.fire({
                title: data.title,
                text: data.message,
                icon: data.icon,                
                showCancelButton: "OK",                
                confirmButtonColor: "#19e207",
                cancelButtonColor: "#ea0907",
                confirmButtonText: data.buttonMessage, // Cambiamos el texto del botón
                cancelButtonText:"Ignore"
            }).then((result) => {
                if (result.isConfirmed) {
                window.open(data.extra_info, '_blank'); // Abre la URL en una nueva pestaña
                }
            });
        }
        else if ( user == data.agent.username &&  ['signedConsent', 'signedIncomeLetter'].includes(data.event_type)) {
            let timerInterval;
            Swal.fire({
                title: "Signed consent",
                text: data.message,
                icon: "info",
                imageWidth: 400,
                imageHeight: 200,
                timer: 10000, // 10 segundos
                timerProgressBar: true,
                allowOutsideClick: false,
                didOpen: () => {
                    Swal.showLoading();
                    timerInterval = setInterval(() => {}, 100);
                },
                willClose: () => {
                    clearInterval(timerInterval);
                }
            }).then(() => {
                Swal.fire({
                    title: "Go to client information",
                    text: "The PDF has been generated successfully.",
                    icon: "success",
                    confirmButtonColor: "#19e207",
                    cancelButtonColor: "#ea0907",
                    confirmButtonText: "Go to information Client",
                    cancelButtonText: "Ignore",
                    showCancelButton: true
                }).then((result) => {
                    if (result.isConfirmed) {
                        window.open(data.absoluteUrl, '_blank'); // Abre la URL en una nueva pestaña
                    }
                });
            });
        }
    };
});
