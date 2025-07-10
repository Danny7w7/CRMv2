document.addEventListener('DOMContentLoaded', function () {
	document.getElementById('smsForm').addEventListener('submit', async function(e) {
		e.preventDefault();

		const formData = new FormData(this);

		Swal.fire({
			title: 'Enviando...',
			text: 'Por favor espera mientras se genera la imagen y se envía el SMS.',
			allowOutsideClick: false,
			didOpen: () => {
				Swal.showLoading();
			}
		});

		try {
			const response = await fetch('/smstemplate/', {
				method: 'POST',
				body: formData
			});

			if (response.ok) {
				let timer;

				Swal.fire({
					icon: 'success',
					title: '¡SMS enviado!',
					text: 'La imagen personalizada fue enviada correctamente.',
					allowOutsideClick: true,
					timer: 4000,
					timerProgressBar: true,
					didOpen: () => {
						timer = setTimeout(() => {
							location.reload();
						}, 4000);
					},
					willClose: () => {
						clearTimeout(timer);
						location.reload();
					}
				});

			} else {
				const data = await response.text();
				Swal.fire({
					icon: 'error',
					title: 'Error al enviar',
					text: `Hubo un error al enviar el SMS.`
				});
			}
		} catch (error) {
			Swal.fire({
				icon: 'error',
				title: 'Fallo de conexión',
				text: 'No se pudo conectar al servidor.'
			});
		}
	});
});
