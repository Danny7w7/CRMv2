// Renderizar la gráfica con ApexCharts
function renderChart(chartData) {
    // Función para generar colores HSL
    function generarColoresPorAgente(numeroDeAgentes) {
        const colores = [];
        const paso = 360 / numeroDeAgentes;
        
        for (let i = 0; i < numeroDeAgentes; i++) {
            // Color para Active Obama (más saturado)
            colores.push(`hsl(${i * paso}, 75%, 45%)`);
            // Color para Active Supp (menos saturado, mismo tono)
            colores.push(`hsl(${i * paso}, 55%, 55%)`);
        }
        
        return colores;
    }

    // Preparar las series para ApexCharts
    const series = [];

    const numAgentes = Object.keys(chartData.series).length;
    const colores = generarColoresPorAgente(numAgentes);

    for (const [agentName, data] of Object.entries(chartData.series)) {
        series.push({
            name: `${agentName} - Active Obama`,
            data: data.activeObama
        });
        series.push({
            name: `${agentName} - Active Supp`,
            data: data.activeSupp
        });
    }

    const options = {
        chart: {
            type: 'line',
            height: 400,
            zoom: {
                enabled: false
            }
        },
        series: series,
        xaxis: {
            categories: chartData.labels,
            title: {
                text: 'Week'
            }
        },
        yaxis: {
            title: {
                text: 'Number of active policies'
            },
            min: 0,
            tickAmount: 5
        },
        stroke: {
            curve: 'smooth',
            width: 2
        },
        colors: colores,  // Colores para las series
        markers: {
            size: 5
        },
        tooltip: {
            theme: "dark",
            enabled: true,
            shared: true,
            intersect: false
        },
        legend: {
            position: 'right'
        }
    };

    const chart = new ApexCharts(document.querySelector("#activeChart"), options);
    chart.render();

    // Estilos CSS para asegurar visibilidad en fondo oscuro
    const style = document.createElement('style');
    style.innerHTML = `
        .apexcharts-menu-icon {
            color: white !important;
        }
        .apexcharts-menu {
            background-color: #333 !important;
            color: white !important;
        }
        .apexcharts-menu .apexcharts-menu-item {
            color: white !important;
        }
        .apexcharts-menu .apexcharts-menu-item:hover {
            background-color: #444 !important;
        }
    `;
    document.head.appendChild(style);
}

// Renderizar la gráfica cuando el modal se muestre
document.getElementById('chartModal').addEventListener('shown.bs.modal', function () {
    const chartData = JSON.parse(document.getElementById("chartData").textContent);
    renderChart(chartData);
});
