document.addEventListener("DOMContentLoaded", function () {
    const form = document.querySelector("#date-filter-form"); // le damos id al form
    if (!form) return;

    form.addEventListener("submit", function (e) {
        e.preventDefault();

        const start_date = document.getElementById("start_date").value;
        const end_date = document.getElementById("end_date").value;

        fetch(form.dataset.url + "?start_date=" + start_date + "&end_date=" + end_date, {
            headers: {
                "X-Requested-With": "XMLHttpRequest"  // para que Django sepa que es fetch
            }
        })
        .then(response => response.json())
        .then(data => {
            // Actualizar tabla Obama
            const tbodyObama = document.querySelector("#tableProfiling tbody");
            tbodyObama.innerHTML = "";
            data.obama.forEach(item => {
                tbodyObama.innerHTML += `<tr><td>${item.profiling}</td><td>${item.count}</td></tr>`;
            });

            // Actualizar tabla Supp
            const tbodySupp = document.querySelector("#tableProfilingSupp tbody");
            tbodySupp.innerHTML = "";
            data.supp.forEach(item => {
                tbodySupp.innerHTML += `<tr><td>${item.status}</td><td>${item.count}</td></tr>`;
            });
        })
        .catch(error => console.error("Error:", error));
    });

});
