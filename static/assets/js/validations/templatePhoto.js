document.addEventListener('DOMContentLoaded', function () {
    // Registrar plugins
    FilePond.registerPlugin(
        FilePondPluginFileValidateType,
        FilePondPluginImagePreview
    );

    // Crear instancia FilePond
    const pond = FilePond.create(document.querySelector('input.filepond'), {
        name: 'filepond',
        allowMultiple: false,
        maxFiles: 1,
        instantUpload: false,
        server: null,
        storeAsFile: true, // 👈 IMPORTANTE
        acceptedFileTypes: ['image/*'],
        allowImagePreview: true,
        labelIdle: 'Arrastra tu imagen o <span class="filepond--label-action">búscala</span>',
        labelFileTypeNotAllowed: 'Solo se permiten imágenes',
        fileValidateTypeDetectType: (source, type) => new Promise((resolve) => resolve(type))
    });

    // Mostrar campos si seleccionan "WELCOME"
    const smsSelect = document.getElementById('sms');
    const welcomeFields = document.getElementById('welcome-fields');

    if (smsSelect) {
        smsSelect.addEventListener('change', function () {
            welcomeFields.style.display = this.value === '6' ? 'block' : 'none';
        });
    }

    // Validar que haya imagen si es WELCOME
    const form = document.getElementById('smsForm');
    if (form) {
        form.addEventListener('submit', function (e) {
            if (smsSelect.value === '6' || smsSelect.value === '11' && pond.getFiles().length === 0) {
                e.preventDefault();
                alert('Debes seleccionar una imagen para el mensaje de bienvenida.');
            }
        });
    }
});
