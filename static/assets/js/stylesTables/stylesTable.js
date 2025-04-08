document.addEventListener("DOMContentLoaded", function() {
    var username = document.body.getAttribute("data-user-role"); // Obtener el nombre de usuario

    if (username === "S" ) { 
        var table1 = $('#tableClient').DataTable({
            lengthChange: false,
            buttons: ['excel', 'print']
        });
        table1.buttons().container().appendTo('#tableClient_wrapper .col-md-6:eq(0)');

        var table2 = $('#tableClient2').DataTable({
            lengthChange: false,
            buttons: ['excel', 'print']
        });
        table2.buttons().container().appendTo('#tableClient2_wrapper .col-md-6:eq(0)');
    } else {
        $('#tableClient').DataTable();
        $('#tableClient2').DataTable();
    }
});
