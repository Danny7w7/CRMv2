document.addEventListener("DOMContentLoaded", function () {
  const dataElement = document.getElementById("agent-data");
  const startDate = dataElement.dataset.startDate;
  const endDate = dataElement.dataset.endDate;

  document.querySelectorAll(".open-agent-modal").forEach(link => {
    link.addEventListener("click", function (e) {
      e.preventDefault();

      const agentId = this.dataset.agentId;
      const agentName = this.dataset.agentName;

      if (!agentId) {
        console.error("El ID del agente es requerido.");
        return;
      }

      document.getElementById("agentModalLabel").textContent = `Ventas de ${agentName}`;
      document.getElementById("modalAgentBody").innerHTML = "Cargando...";

      fetch(`/sale/detalleAgente/?agent_id=${agentId}&start_date=${startDate}&end_date=${endDate}`)
        .then(response => response.text())
        .then(html => {
          document.getElementById("modalAgentBody").innerHTML = html;
          const modal = new bootstrap.Modal(document.getElementById('agentModal'));
          modal.show();
        })
        .catch(() => {
          document.getElementById("modalAgentBody").innerHTML = "Error al cargar la información.";
        });
    });
  });
});
