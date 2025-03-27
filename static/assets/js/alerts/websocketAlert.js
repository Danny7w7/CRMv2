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

        if ( userRole === "A" || userRole === "Admin" && data.event_type === 'newMessage' && !window.location.href.includes("chatSms")) {

            if (user == data.agent.username || userRole === "Admin" ) {
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
        }

        if ( userRole === "A"  && data.event_type === 'newAccionRequired' ) {

            if (user == data.agent.username  ) {
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
        }

        if (userRole === "S" || userRole === "C" || userRole === "Admin" && data.event_type === 'actionCompleted') {

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

    };
});
