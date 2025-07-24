

$(document).ready(function() {
    const cardsPerPage = 9; // Número de planes por página (3 columnas * 3 filas = 9)
    let currentPage = 1;
    const $planCards = $('.plan-card'); // Obtiene todas las tarjetas de planes
    const totalCards = $planCards.length;
    const totalPages = Math.ceil(totalCards / cardsPerPage);
    const $paginationControls = $('#pagination-controls');

    // Función para mostrar la página actual de planes
    function showPage(pageNumber) {
        $planCards.hide(); // Oculta todas las tarjetas
        const startIndex = (pageNumber - 1) * cardsPerPage;
        const endIndex = startIndex + cardsPerPage;
        $planCards.slice(startIndex, endIndex).show(); // Muestra solo las tarjetas de la página actual

        // Actualiza el estado activo de los botones de paginación
        $paginationControls.find('li').removeClass('active');
        $paginationControls.find(`li:eq(${pageNumber})`).addClass('active'); // +1 porque el índice 0 es el "Prev"
    }

    // Función para generar los controles de paginación
    function setupPagination() {
        if (totalCards <= cardsPerPage) { // Si hay menos o igual planes que los que caben en una página, no mostrar paginación
            $paginationControls.parent().hide(); // Oculta la navegación completa
            return;
        }

        // Botón "Anterior"
        $paginationControls.append(`<li class="page-item"><a class="page-link" href="#" data-page="prev">Anterior</a></li>`);

        // Botones numéricos
        for (let i = 1; i <= totalPages; i++) {
            $paginationControls.append(`<li class="page-item"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`);
        }

        // Botón "Siguiente"
        $paginationControls.append(`<li class="page-item"><a class="page-link" href="#" data-page="next">Siguiente</a></li>`);

        // Manejar clics en los botones de paginación
        $paginationControls.on('click', 'a.page-link', function(e) {
            e.preventDefault(); // Evitar que el enlace recargue la página
            const clickedPage = $(this).data('page');

            if (clickedPage === 'prev') {
                currentPage = Math.max(1, currentPage - 1);
            } else if (clickedPage === 'next') {
                currentPage = Math.min(totalPages, currentPage + 1);
            } else {
                currentPage = parseInt(clickedPage);
            }
            showPage(currentPage);
            updatePaginationControls();
        });

        // Función para habilitar/deshabilitar botones Anterior/Siguiente
        function updatePaginationControls() {
            $paginationControls.find('[data-page="prev"]').parent().toggleClass('disabled', currentPage === 1);
            $paginationControls.find('[data-page="next"]').parent().toggleClass('disabled', currentPage === totalPages);
        }

        // Mostrar la primera página al cargar
        showPage(currentPage);
        updatePaginationControls();
    }

    // Inicializar la paginación solo si hay planes para mostrar
    if (totalCards > 0) {
        setupPagination();
    }
});