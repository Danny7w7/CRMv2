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
        storeAsFile: true,
        acceptedFileTypes: ['image/*'],
        allowImagePreview: true,
        labelIdle: 'Drag your image or <span class="filepond--label-action">look for it</span>',
        labelFileTypeNotAllowed: 'Only images are allowed.',
        fileValidateTypeDetectType: (source, type) => new Promise((resolve) => resolve(type))
    });

    const smsSelect = document.getElementById('sms');
    const welcomeFields = document.getElementById('welcome-fields');

    if (smsSelect) {
        smsSelect.addEventListener('change', function () {
            welcomeFields.style.display = (this.value === '6' || this.value === '11') ? 'block' : 'none';
        });
    }

    const form = document.getElementById('smsForm');
    if (form) {
        form.addEventListener('submit', function (e) {
            if ((smsSelect.value === '6' || smsSelect.value === '11') && pond.getFiles().length === 0) {
                e.preventDefault();
                alert('You must select an image for the welcome message.');
            }
        });
    }
});
