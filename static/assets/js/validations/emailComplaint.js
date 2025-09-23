const selects = document.querySelectorAll(
    "#firstConsent",
    "#lastConsent",
    "#complaint"
);
const form = document.getElementById("emailComplaintForm");

selects.forEach((select) => {
    select.addEventListener("change", function () {
        const selectedOption = this.options[this.selectedIndex];
        const id = selectedOption.value;
        const url = selectedOption.getAttribute("data-url");
        let link;
        if (select.id == "firstConsent") {
            link = document.getElementById("viewFirstConsent");
        } else if (select.id == "lastConsent") {
            link = document.getElementById("viewLastConsent");
        } else if (select.id == "complaint") {
            link = document.getElementById("viewComplaint");
        }
        link.href = url;
    });
});

form.addEventListener("submit", function (event) {
  event.preventDefault();
  const formData = new FormData(form);

  let timerInterval;

  showOrHideModal("modalEmailComplaint", false); // cerramos el modal del formulario

  Swal.fire({
    title: "Sending...",
    html: "We will finish in <b></b> milliseconds.",
    timer: 20000, // 10 segundos maximo de espera
    timerProgressBar: true,
    allowOutsideClick: false,
    didOpen: () => {
      Swal.showLoading();
      const timer = Swal.getPopup().querySelector("b");
      timerInterval = setInterval(() => {
        timer.textContent = `${Swal.getTimerLeft()}`;
      }, 100);
    },
    willClose: () => {
      clearInterval(timerInterval);
    },
  });

  fetch("/sendEmailComplaint/", {
    method: "POST",
    body: formData,
  })
  .then((response) => response.json())
  .then((data) => {
    Swal.close(); // cerramos el loader
    if (data.success) {
      Swal.fire({
        icon: "success",
        title: "Success!",
        text: data.message || "Your complaint was sent successfully.",
      });
    } else {
      Swal.fire({
        icon: "error",
        title: "Error",
        text: data.message || "Something went wrong. Please try again.",
      });
    }
  })
  .catch((error) => {
    Swal.close(); // cerramos el loader
    Swal.fire({
      icon: "error",
      title: "Request Failed",
      text: error.message || "An unexpected error occurred.",
    });
  });
});

function showOrHideModal(modalId, show = true) {
  const modal = document.getElementById(modalId);

  if (!modal) {
    console.error(`Modal with ID ${modalId} not found.`);
    return;
  }

  // Intenta obtener la instancia existente primero
  let bsModal = bootstrap.Modal.getInstance(modal);

  // Si no existe instancia, créala
  if (!bsModal) {
    bsModal = new bootstrap.Modal(modal);
  }

  if (show) {
    bsModal.show();
  } else {
    bsModal.hide();
  }
}
