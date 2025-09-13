document.addEventListener("DOMContentLoaded", function() {
    var username = document.body.getAttribute("data-user-role");

    function initDataTable(selector, withButtons = false) {
        if ($(selector).length) {
            if (withButtons) {
                var table = $(selector).DataTable({
                    lengthChange: false,
                    buttons: ['excel', 'print']
                });
                table.buttons().container().appendTo(`${selector}_wrapper .col-md-6:eq(0)`);
            } else {
                $(selector).DataTable();
            }
        }
    }

    if (username === "S") {
        initDataTable('#tableClient', true);
        initDataTable('#tableClient2', true);
    } else {
        initDataTable('#tableClient');
        initDataTable('#tableClient2');
    }
});
