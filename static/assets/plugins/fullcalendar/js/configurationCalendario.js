// static/js/calendar.js

class CalendarManager {
    constructor(events, userRole, isSuperuser) {
        this.events = events;
        this.userRole = userRole;
        this.isSuperuser = isSuperuser;
        this.calendar = null;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initCalendar();
        });
    }

    initCalendar() {
        const calendarEl = document.getElementById('calendar');
        
        this.calendar = new FullCalendar.Calendar(calendarEl, {
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
            },
            initialView: 'dayGridMonth',
            locale: 'es',
            navLinks: true,
            selectable: true,
            nowIndicator: true,
            dayMaxEvents: false, // Mostrar todos los eventos, no limitar
            editable: false,
            selectable: true,
            businessHours: true,
            
            // Configuración para mostrar eventos como bloques en lugar de puntos
            dayMaxEventRows: false, // No limitar filas
            moreLinkClick: 'popover', // Mostrar popover si hay muchos eventos
            
            events: this.events,
            
            eventClick: (info) => this.handleEventClick(info),
            eventDidMount: (info) => this.handleEventMount(info),
            
            height: 'auto',
            dayHeaderFormat: { weekday: 'short' },
            eventTimeFormat: {
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
            },
            
            // Configurar la visualización de eventos
            eventDisplay: 'block', // Forzar que se muestren como bloques
            displayEventTime: true, // Mostrar la hora en el evento
            displayEventEnd: false, // No mostrar hora de fin
            
            // Personalizar el contenido del evento
            eventContent: function(arg) {
                return {
                    html: `<div class="fc-event-time">${arg.timeText}</div>
                           <div class="fc-event-title">${arg.event.title}</div>`
                };
            }
        });
        
        this.calendar.render();
    }

    handleEventClick(info) {
        const event = info.event;
        const props = event.extendedProps;
        
        // Llenar el modal con información del evento
        this.setModalContent(event, props);
        
        // Configurar enlaces
        this.setModalLinks(props);
        
        // Mostrar modal
        this.showModal();
    }

    setModalContent(event, props) {
        const elements = {
            'modal-client-name': props.client_name,
            'modal-client-phone' : props.client_phone,
            'modal-agent-name': props.agent_name,
            'modal-date': props.datetime || new Date(event.start).toLocaleDateString(),
            'modal-time': props.time || new Date(event.start).toLocaleTimeString(),
            'modal-content': props.content
        };

        // Llenar elementos básicos
        Object.keys(elements).forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = elements[id];
            }
        });

        // Elementos condicionales según rol
        if (this.userRole === 'Admin') {
            const statusElement = document.getElementById('modal-status');
            if (statusElement) {
                statusElement.textContent = props.is_active ? 'Activo' : 'Inactivo';
            }
        }

        if (this.isSuperuser) {
            const companyElement = document.getElementById('modal-company');
            if (companyElement) {
                companyElement.textContent = props.company_name;
            }
        }
    }

    setModalLinks(props) {
        const editLink = document.getElementById('edit-link');
        const toggleLink = document.getElementById('toggle-link');
        
        if (editLink) editLink.href = props.edit_url;
        if (toggleLink) toggleLink.href = props.toggle_url;
    }

    showModal() {
        const modalElement = document.getElementById('eventModal');
        if (modalElement && typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(modalElement);
            modal.show();
        }
    }

    handleEventMount(info) {
        // Agregar tooltip con información completa
        const props = info.event.extendedProps;
        const startDate = new Date(info.event.start);
        
        const tooltipText = [
            `Cliente: ${props.client_name}`,
            `Phone: ${props.client_phone}`,
            `Agente: ${props.agent_name}`,
            `Fecha: ${props.datetime || startDate.toLocaleDateString()}`,
            `Hora: ${props.time || startDate.toLocaleTimeString()}`,
            `Observación: ${props.content}`
        ].join('\n');
        
        info.el.setAttribute('title', tooltipText);
    }

    // Métodos públicos para interactuar con el calendario
    refreshCalendar() {
        if (this.calendar) {
            this.calendar.refetchEvents();
        }
    }

    changeView(viewName) {
        if (this.calendar) {
            this.calendar.changeView(viewName);
        }
    }

    goToDate(date) {
        if (this.calendar) {
            this.calendar.gotoDate(date);
        }
    }
}

// Función de inicialización global
window.initCalendar = function(events, userRole, isSuperuser) {
    new CalendarManager(events, userRole, isSuperuser);
};